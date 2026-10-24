"""
HDFury device implementation.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import json
import logging

from ucapi_framework import PersistentConnectionDevice

from uc_intg_hdfury.config import HDFuryConfig
from uc_intg_hdfury.models import ModelConfig, get_model_config, get_source_list

_LOG = logging.getLogger(__name__)

RESPONSE_TIMEOUT = 3.0
WRITE_TIMEOUT = 0.8
HEARTBEAT_INTERVAL = 20

HTTP_TIMEOUT = 4.0
EXTENDED_MODELS = ("vrroom", "vertex2")
OPERATION_MODES = {
    "0": "Mode 0 - Splitter TX0/TX1 FRL5 VRR",
    "1": "Mode 1 - Splitter TX0/TX1 UPSCALE FRL5",
    "2": "Mode 2 - Matrix TMDS",
    "3": "Mode 3 - Matrix FRL->TMDS",
    "4": "Mode 4 - Matrix DOWNSCALE",
    "5": "Mode 5 - Matrix RX0:FRL5 + RX1-3:TMDS",
}

ERROR_MARKERS = ("unknown", "invalid", "error", "unsupported", "not found", "usage")

SETTING_KEYS = {
    "edid": "edidmode",
    "hdcp": "hdcp",
    "edid_audio": "edidaudio",
    "earc_force": "earcforce",
    "arc_force": "arcforce",
    "audio_mode": "audiomode",
    "led_mode": "led",
    "color_space": "colorspace",
    "deep_color": "deepcolor",
    "output_resolution": "outres",
}


class HDFuryDevice(PersistentConnectionDevice):
    """HDFury device using persistent TCP connection."""

    def __init__(self, device_config: HDFuryConfig, **kwargs):
        super().__init__(device_config, **kwargs)
        self._config = device_config
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()
        self._connect_lock = asyncio.Lock()

        self.model_config: ModelConfig = get_model_config(device_config.model_id)
        self.source_list: list[str] = get_source_list(self.model_config)

        self._state = "UNAVAILABLE"
        self._current_source: str | None = None
        self._sensor_values: dict[str, str] = {}
        self._settings: dict[str, str] = {}
        self._silent_keys: set[str] = set()
        self.firmware: str | None = None

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

    @property
    def state(self) -> str:
        return self._state

    @property
    def scale_key(self) -> str:
        return "scalemode" if self.model_config.model_id == "arcana2" else "scale"

    async def connect(self) -> bool:
        async with self._connect_lock:
            return await super().connect()

    async def disconnect(self) -> None:
        async with self._connect_lock:
            await super().disconnect()
            self._state = "UNAVAILABLE"
            self.push_update()

    async def establish_connection(self):
        await self._close_tcp()

        _LOG.info("%s Connecting to %s:%d", self.log_id, self._config.address, self._config.port)

        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self._config.address, self._config.port),
            timeout=10.0,
        )

        await self._drain_buffer()

        version = await self._send_command("get ver")
        if version:
            self.firmware = version.replace("ver", "", 1).strip() or version
            _LOG.info("%s Connected, firmware: %s", self.log_id, version)
        else:
            _LOG.info("%s Connected", self.log_id)

        self._state = "ON"
        self.push_update()
        return (self._reader, self._writer)

    async def close_connection(self):
        _LOG.info("%s Disconnecting", self.log_id)
        await self._close_tcp()
        if self._state != "UNAVAILABLE":
            self._state = "UNAVAILABLE"
            self.push_update()

    async def _close_tcp(self):
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
        asyncio.create_task(self._poll_state())

        while self._reader and self._writer and not self._reader.at_eof():
            try:
                await asyncio.sleep(HEARTBEAT_INTERVAL)

                if not self._reader or not self._writer or self._reader.at_eof():
                    _LOG.warning("%s Connection EOF detected", self.log_id)
                    break

                async with self._lock:
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
        if timeout == RESPONSE_TIMEOUT and self._is_write(command):
            timeout = WRITE_TIMEOUT

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
                    if self._is_write(command):
                        return ""
                    return None

                return result_lines[0]

            except asyncio.TimeoutError:
                if self._is_write(command):
                    return ""
                return None
            except (ConnectionError, OSError, BrokenPipeError):
                return None
            except Exception as err:
                _LOG.debug("%s Command '%s' failed: %s", self.log_id, command, err)
                return None

    async def _poll_state(self) -> None:
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

        self._store_status("video_input", await self._send_command("get status rx0"), "RX0")
        self._store_status("audio_rx", await self._send_command("get status audout"), "AUDOUT")

        if self.model_config.matrix_outputs and self.model_config.matrix_outputs >= 1:
            self._store_status("video_tx0", await self._send_command("get status tx0"), "TX0")
            self._store_status("sink_tx0", await self._send_command("get status tx0sink"), "TX0SINK")

            self._sensor_values["audio_tx0"] = await self._get_audio_tx(0)

        if self.model_config.matrix_outputs and self.model_config.matrix_outputs >= 2:
            self._store_status("video_tx1", await self._send_command("get status tx1"), "TX1")
            self._store_status("sink_tx1", await self._send_command("get status tx1sink"), "TX1SINK")

            self._sensor_values["audio_tx1"] = await self._get_audio_tx(1)

        if self.model_config.model_id in EXTENDED_MODELS:
            await self._poll_extended()
        self.push_update()
        await self._poll_settings()
        self.push_update()

    async def _poll_extended(self) -> None:
        self._store_status("video_rx1", await self._send_command("get status rx1"), "RX1")

        response = await self._send_command("get opmode")
        parts = response.split() if response else []
        if len(parts) >= 2 and parts[0].lower() == "opmode":
            self._sensor_values["operation_mode"] = OPERATION_MODES.get(parts[1], f"Mode {parts[1]}")

        info = await self._http_json("/ssi/infopage.ssi")
        if info:
            earc = str(info.get("EARCRX", "")).strip()
            if earc:
                self._sensor_values["earc_rx"] = earc
            caps = str(info.get("EDIDA0", "")).strip()
            if caps:
                self._sensor_values["sink_audio_tx0"] = caps

    async def _http_get(self, path: str) -> str | None:
        writer = None
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._config.address, 80), timeout=HTTP_TIMEOUT
            )
            request = (
                f"GET {path} HTTP/1.0\r\n"
                f"Host: {self._config.address}\r\n"
                "Connection: close\r\n\r\n"
            )
            writer.write(request.encode("ascii"))
            await writer.drain()
            raw = await asyncio.wait_for(reader.read(), timeout=HTTP_TIMEOUT)
        except (OSError, asyncio.TimeoutError):
            return None
        finally:
            if writer:
                writer.close()
        head, _, body = raw.partition(b"\r\n\r\n")
        status_line = head.split(b"\r\n", 1)[0]
        if b" 200" not in status_line:
            return None
        return body.decode("utf-8", errors="replace")

    async def _http_json(self, path: str) -> dict | None:
        body = await self._http_get(path)
        if not body:
            return None
        try:
            data = json.loads(body)
        except ValueError:
            return None
        return data if isinstance(data, dict) else None

    def _store_status(self, key: str, response: str | None, prefix: str) -> None:
        if not response:
            return
        head, sep, tail = response.partition(":")
        if sep and head.strip().upper() == prefix:
            self._sensor_values[key] = tail.strip()

    async def _poll_settings(self) -> None:
        for key, cmd in SETTING_KEYS.items():
            if self._supports_setting(key):
                await self._read_setting(key, cmd)
        if self.model_config.scale_modes:
            await self._read_setting("scale_mode", self.scale_key)

    def _supports_setting(self, key: str) -> bool:
        model = self.model_config
        supported = {
            "edid": model.edid_modes,
            "hdcp": model.hdcp_modes,
            "edid_audio": model.edid_audio_sources,
            "earc_force": model.earc_force_modes,
            "arc_force": model.arc_force_modes,
            "audio_mode": model.audio_modes,
            "led_mode": model.led_modes,
            "color_space": model.color_space_modes,
            "deep_color": model.deep_color_modes,
            "output_resolution": model.output_resolutions,
        }
        return bool(supported.get(key))

    async def _read_setting(self, key: str, cmd: str) -> None:
        if cmd in self._silent_keys:
            return
        response = await self._send_command(f"get {cmd}", timeout=1.0)
        if not response:
            self._silent_keys.add(cmd)
            return
        if self._is_error(response):
            return
        parts = response.split()
        if parts and parts[0].lower() == cmd:
            parts = parts[1:]
        if parts:
            self._settings[key] = parts[0]

    @staticmethod
    def _is_write(command: str) -> bool:
        return command.startswith("set ") or command in ("hotplug", "reboot")

    @staticmethod
    def _is_error(response: str) -> bool:
        lowered = response.lower()
        return any(marker in lowered for marker in ERROR_MARKERS)

    def get_setting(self, key: str) -> str | None:
        return self._settings.get(key)

    async def _get_audio_tx(self, output: int) -> str:
        mode_resp = await self._send_command(f"get audiomodetx{output}")
        mode = ""
        if mode_resp and f"audiomodetx{output}" in mode_resp:
            parts = mode_resp.split(None, 1)
            if len(parts) >= 2:
                mode = parts[1]

        status_resp = await self._send_command(f"get status aud{output}")
        if status_resp and f"AUD{output}:" in status_resp:
            audio_info = status_resp.replace(f"AUD{output}:", "").strip()
            if audio_info:
                return audio_info
        return mode

    def get_sensor_value(self, key: str) -> str | None:
        if key == "firmware":
            return self.firmware
        return self._sensor_values.get(key)

    async def send_command(self, command: str) -> bool:
        result = await self._send_command(command)
        return result is not None

    async def _set(self, setting: str, cmd: str, value: str) -> bool:
        result = await self._send_command(f"set {cmd} {value}")
        if result is None or (result and self._is_error(result)):
            return False
        self._settings[setting] = value
        self.push_update()
        return True

    async def set_source(self, source: str) -> bool:
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
            self.push_update()
            return True
        return False

    async def set_edid_mode(self, mode: str) -> bool:
        return await self._set("edid", "edidmode", mode)

    async def set_hdcp_mode(self, mode: str) -> bool:
        if mode == "14":
            mode = "1.4"
        return await self._set("hdcp", "hdcp", mode)

    async def set_hdr_custom(self, enabled: bool) -> bool:
        result = await self._send_command(f"set hdrcustom {'on' if enabled else 'off'}")
        return result is not None

    async def set_hdr_disable(self, enabled: bool) -> bool:
        result = await self._send_command(f"set hdrdisable {'on' if enabled else 'off'}")
        return result is not None

    async def set_cec(self, enabled: bool) -> bool:
        result = await self._send_command(f"set cec {'on' if enabled else 'off'}")
        return result is not None

    async def set_earc_force(self, mode: str) -> bool:
        return await self._set("earc_force", "earcforce", mode)

    async def set_arc_force(self, mode: str) -> bool:
        return await self._set("arc_force", "arcforce", mode)

    async def set_oled(self, enabled: bool) -> bool:
        result = await self._send_command(f"set oled {'on' if enabled else 'off'}")
        return result is not None

    async def set_autoswitch(self, enabled: bool) -> bool:
        result = await self._send_command(f"set autosw {'on' if enabled else 'off'}")
        return result is not None

    async def set_scale_mode(self, mode: str) -> bool:
        return await self._set("scale_mode", self.scale_key, mode)

    async def _action(self, name: str) -> bool:
        if await self._http_get(f"/cmd?{name}=") is not None:
            _LOG.info("%s Sent '%s' via HTTP", self.log_id, name)
            return True
        for command in (name, f"set {name}"):
            result = await self._send_command(command)
            if result is None:
                continue
            if result and self._is_error(result):
                continue
            _LOG.info("%s Sent '%s' via TCP", self.log_id, command)
            return True
        _LOG.warning("%s Action '%s' failed", self.log_id, name)
        return False

    async def hotplug(self) -> bool:
        return await self._action("hotplug")

    async def reboot(self) -> bool:
        return await self._action("reboot")

    async def set_edid_audio(self, source: str) -> bool:
        return await self._set("edid_audio", "edidaudio", source)

    async def set_audio_mode(self, mode: str) -> bool:
        return await self._set("audio_mode", "audiomode", mode)

    async def set_led_mode(self, mode: str) -> bool:
        return await self._set("led_mode", "led", mode)

    async def set_color_space(self, mode: str) -> bool:
        return await self._set("color_space", "colorspace", mode)

    async def set_deep_color(self, mode: str) -> bool:
        return await self._set("deep_color", "deepcolor", mode)

    async def set_output_resolution(self, resolution: str) -> bool:
        return await self._set("output_resolution", "outres", resolution)
