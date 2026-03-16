"""
HDFury device implementation.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging

from ucapi_framework import PersistentConnectionDevice, DeviceEvents

from uc_intg_hdfury.config import HDFuryConfig
from uc_intg_hdfury.models import ModelConfig, get_model_config, get_source_list

_LOG = logging.getLogger(__name__)

RESPONSE_TIMEOUT = 3.0
HEARTBEAT_INTERVAL = 20


class HDFuryDevice(PersistentConnectionDevice):
    """HDFury device using persistent TCP connection."""

    def __init__(self, device_config: HDFuryConfig, **kwargs):
        super().__init__(device_config, **kwargs)
        self._config = device_config
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()

        self.model_config: ModelConfig = get_model_config(device_config.model_id)
        self.source_list: list[str] = get_source_list(self.model_config)

        self._state = "ON"
        self._current_source: str | None = None
        self._sensor_values: dict[str, str] = {}

    @property
    def identifier(self) -> str:
        return self._config.identifier

    @property
    def name(self) -> str:
        return self._config.name

    @property
    def address(self) -> str:
        return self._config.address

    @property
    def log_id(self) -> str:
        return f"[{self.name}]"

    @property
    def current_source(self) -> str | None:
        return self._current_source

    async def establish_connection(self):
        """Establish TCP connection to HDFury device."""
        await self._close_tcp()

        _LOG.info("%s Connecting to %s:%d", self.log_id, self._config.address, self._config.port)

        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self._config.address, self._config.port),
            timeout=10.0,
        )

        await self._drain_buffer()

        version = await self._send_command("get ver")
        if version:
            _LOG.info("%s Connected, firmware: %s", self.log_id, version)
        else:
            _LOG.info("%s Connected", self.log_id)

        self._state = "ON"
        await self._poll_state()
        return (self._reader, self._writer)

    async def close_connection(self):
        """Close TCP connection."""
        _LOG.info("%s Disconnecting", self.log_id)
        await self._close_tcp()

    async def _close_tcp(self):
        """Close TCP socket if open."""
        writer = self._writer
        self._reader = None
        self._writer = None
        if writer:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _drain_buffer(self):
        """Drain any pending data from the TCP read buffer."""
        if not self._reader:
            return
        try:
            while True:
                data = await asyncio.wait_for(self._reader.read(4096), timeout=0.3)
                if not data:
                    break
        except asyncio.TimeoutError:
            pass

    async def maintain_connection(self):
        """Maintain connection with periodic heartbeat and state polling."""
        while self._reader and self._writer and not self._reader.at_eof():
            try:
                await asyncio.sleep(HEARTBEAT_INTERVAL)

                if not self._reader or not self._writer or self._reader.at_eof():
                    _LOG.warning("%s Connection EOF detected", self.log_id)
                    break

                await self._drain_buffer()

                version = await self._send_command("get ver")
                if not version:
                    _LOG.warning("%s Heartbeat failed", self.log_id)
                    break

                await self._poll_state()

            except asyncio.CancelledError:
                raise
            except (ConnectionError, OSError, BrokenPipeError) as err:
                _LOG.warning("%s Connection lost: %s", self.log_id, err)
                break
            except Exception as err:
                _LOG.error("%s Connection error: %s", self.log_id, err)
                break

        await self._close_tcp()

    async def _send_command(self, command: str, timeout: float = RESPONSE_TIMEOUT) -> str | None:
        """Send command and return response, reading all available lines."""
        async with self._lock:
            if not self._writer or not self._reader:
                return None

            if self._writer.is_closing() or self._reader.at_eof():
                return None

            try:
                self._writer.write(f"{command}\r\n".encode("ascii"))
                await self._writer.drain()

                result_lines = []
                deadline = asyncio.get_event_loop().time() + timeout

                while True:
                    remaining = deadline - asyncio.get_event_loop().time()
                    if remaining <= 0:
                        break

                    try:
                        line = await asyncio.wait_for(
                            self._reader.readline(),
                            timeout=min(remaining, 1.0),
                        )
                    except asyncio.TimeoutError:
                        if result_lines:
                            break
                        continue

                    if not line:
                        break

                    decoded = line.decode("ascii", errors="replace").strip()
                    if not decoded or decoded == ">":
                        if result_lines:
                            break
                        continue

                    cleaned = decoded.replace(">", "").strip()
                    if cleaned:
                        result_lines.append(cleaned)
                        break

                if not result_lines:
                    if command.startswith("set "):
                        return ""
                    return None

                return result_lines[0]

            except asyncio.TimeoutError:
                if command.startswith("set "):
                    return ""
                return None
            except (ConnectionError, OSError, BrokenPipeError):
                return None
            except Exception as err:
                _LOG.debug("%s Command '%s' failed: %s", self.log_id, command, err)
                return None

    async def _poll_state(self) -> None:
        """Poll device state and update sensor values."""
        if self.model_config.input_count > 0:
            response = await self._send_command("get insel")
            if response and "insel" in response:
                parts = response.split()
                if len(parts) >= 2:
                    input_num = parts[1]
                    if input_num.isdigit():
                        idx = int(input_num)
                        if 0 <= idx < len(self.source_list):
                            self._current_source = self.source_list[idx]
                            self._sensor_values["current_input"] = self._current_source

        response = await self._send_command("get status rx0")
        if response and "RX0:" in response:
            self._sensor_values["video_input"] = response.replace("RX0:", "").strip()

        response = await self._send_command("get status audiorx")
        if response and "AUDIORX:" in response:
            self._sensor_values["audio_rx"] = response.replace("AUDIORX:", "").strip()

        if self.model_config.matrix_outputs and self.model_config.matrix_outputs >= 1:
            response = await self._send_command("get status tx0")
            if response and "TX0:" in response:
                self._sensor_values["video_tx0"] = response.replace("TX0:", "").strip()

            response = await self._send_command("get status tx0sink")
            if response and "TX0SINK:" in response:
                self._sensor_values["sink_tx0"] = response.replace("TX0SINK:", "").strip()

            response = await self._send_command("get status audiotx0")
            if response and "AUDIOTX0:" in response:
                self._sensor_values["audio_tx0"] = response.replace("AUDIOTX0:", "").strip()

        if self.model_config.matrix_outputs and self.model_config.matrix_outputs >= 2:
            response = await self._send_command("get status tx1")
            if response and "TX1:" in response:
                self._sensor_values["video_tx1"] = response.replace("TX1:", "").strip()

            response = await self._send_command("get status tx1sink")
            if response and "TX1SINK:" in response:
                self._sensor_values["sink_tx1"] = response.replace("TX1SINK:", "").strip()

            response = await self._send_command("get status audiotx1")
            if response and "AUDIOTX1:" in response:
                self._sensor_values["audio_tx1"] = response.replace("AUDIOTX1:", "").strip()

        self._emit_updates()

    def _emit_updates(self) -> None:
        """Emit entity update events for sensors."""
        sensor_map = {
            "current_input": f"sensor.{self.identifier}.current_input",
            "video_input": f"sensor.{self.identifier}.video_input",
            "audio_rx": f"sensor.{self.identifier}.audio_rx",
            "video_tx0": f"sensor.{self.identifier}.video_tx0",
            "sink_tx0": f"sensor.{self.identifier}.sink_tx0",
            "audio_tx0": f"sensor.{self.identifier}.audio_tx0",
            "video_tx1": f"sensor.{self.identifier}.video_tx1",
            "sink_tx1": f"sensor.{self.identifier}.sink_tx1",
            "audio_tx1": f"sensor.{self.identifier}.audio_tx1",
        }

        for key, entity_id in sensor_map.items():
            value = self._sensor_values.get(key)
            if value:
                self.events.emit(
                    DeviceEvents.UPDATE,
                    entity_id,
                    {"state": "ON", "value": value},
                )

    def get_sensor_value(self, key: str) -> str | None:
        """Get sensor value by key."""
        return self._sensor_values.get(key)

    async def send_command(self, command: str) -> bool:
        """Send a command to the device. Returns True on success."""
        result = await self._send_command(command)
        return result is not None

    async def set_source(self, source: str) -> bool:
        """Set input source."""
        if self.model_config.model_id == "vertex":
            source_map = {"Top": "top", "Bottom": "bot"}
            cmd_source = source_map.get(source, "top")
            result = await self._send_command(f"set input {cmd_source}")
        elif self.model_config.source_command:
            source_num = source.replace("HDMI ", "").strip()
            result = await self._send_command(f"set {self.model_config.source_command} {source_num}")
        else:
            return False

        if result is not None:
            self._current_source = source
            self._sensor_values["current_input"] = source
            self._emit_updates()
            return True
        return False

    async def set_edid_mode(self, mode: str) -> bool:
        """Set EDID mode."""
        result = await self._send_command(f"set edidmode {mode}")
        return result is not None

    async def set_hdcp_mode(self, mode: str) -> bool:
        """Set HDCP mode."""
        if mode == "14":
            mode = "1.4"
        result = await self._send_command(f"set hdcp {mode}")
        return result is not None

    async def set_hdr_custom(self, enabled: bool) -> bool:
        """Set HDR custom mode."""
        result = await self._send_command(f"set hdrcustom {'on' if enabled else 'off'}")
        return result is not None

    async def set_hdr_disable(self, enabled: bool) -> bool:
        """Set HDR disable mode."""
        result = await self._send_command(f"set hdrdisable {'on' if enabled else 'off'}")
        return result is not None

    async def set_cec(self, enabled: bool) -> bool:
        """Set CEC state."""
        result = await self._send_command(f"set cec {'on' if enabled else 'off'}")
        return result is not None

    async def set_earc_force(self, mode: str) -> bool:
        """Set eARC force mode."""
        result = await self._send_command(f"set earcforce {mode}")
        return result is not None

    async def set_arc_force(self, mode: str) -> bool:
        """Set ARC force mode."""
        result = await self._send_command(f"set arcforce {mode}")
        return result is not None

    async def set_oled(self, enabled: bool) -> bool:
        """Set OLED display state."""
        result = await self._send_command(f"set oled {'on' if enabled else 'off'}")
        return result is not None

    async def set_autoswitch(self, enabled: bool) -> bool:
        """Set autoswitch state."""
        result = await self._send_command(f"set autosw {'on' if enabled else 'off'}")
        return result is not None

    async def set_scale_mode(self, mode: str) -> bool:
        """Set scale mode."""
        cmd = "scalemode" if self.model_config.model_id == "arcana2" else "scale"
        result = await self._send_command(f"set {cmd} {mode}")
        return result is not None

    async def hotplug(self) -> bool:
        """Trigger hotplug."""
        result = await self._send_command("set hotplug")
        return result is not None

    async def reboot(self) -> bool:
        """Reboot device."""
        result = await self._send_command("set reboot")
        return result is not None

    async def set_edid_audio(self, source: str) -> bool:
        """Set EDID audio source."""
        result = await self._send_command(f"set edidaudio {source}")
        return result is not None

    async def set_audio_mode(self, mode: str) -> bool:
        """Set audio mode (ARCANA2)."""
        result = await self._send_command(f"set audiomode {mode}")
        return result is not None

    async def set_led_mode(self, mode: str) -> bool:
        """Set LED mode (DIVA)."""
        result = await self._send_command(f"set led {mode}")
        return result is not None

    async def set_color_space(self, mode: str) -> bool:
        """Set color space mode."""
        result = await self._send_command(f"set colorspace {mode}")
        return result is not None

    async def set_deep_color(self, mode: str) -> bool:
        """Set deep color mode."""
        result = await self._send_command(f"set deepcolor {mode}")
        return result is not None

    async def set_output_resolution(self, resolution: str) -> bool:
        """Set output resolution (Dr.HDMI 8K)."""
        result = await self._send_command(f"set outres {resolution}")
        return result is not None
