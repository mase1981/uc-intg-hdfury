"""
HDFury Integration for Unfolded Circle Remote Two/3.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""
import asyncio
import logging
from uc_intg_hdfury.models import ModelConfig, format_source_for_command

class HDFuryClient:
    def __init__(self, host: str, port: int, log: logging.Logger, model_config: ModelConfig):
        self.host, self.port, self.log = host, port, log
        self.model_config = model_config
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()
        self._connection_lock = asyncio.Lock()
        self._last_activity = 0.0

    def is_connected(self) -> bool:
        return self._writer is not None and not self._writer.is_closing()

    async def connect(self):
        async with self._connection_lock:
            if self.is_connected():
                return
            self.log.info(f"HDFuryClient: Connecting to {self.host}:{self.port}")
            try:
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port), timeout=10.0)
                try:
                    await asyncio.wait_for(self._reader.read(2048), timeout=1.0)
                    self.log.debug("HDFuryClient: Cleared welcome message from buffer.")
                except asyncio.TimeoutError:
                    pass
                
                self._last_activity = asyncio.get_event_loop().time()
                self.log.info(f"HDFuryClient: Connected successfully.")
            except Exception as e:
                self.log.error(f"HDFuryClient: Connection failed: {e}")
                await self.disconnect()
                raise

    async def disconnect(self):
        if not self._writer:
            return
        self.log.info("HDFuryClient: Disconnecting.")
        self._writer.close()
        try:
            await self._writer.wait_closed()
        except Exception as e:
            self.log.debug(f"HDFuryClient: Error during disconnect: {e}")
        finally:
            self._writer = self._reader = None

    async def _ensure_connection(self):
        current_time = asyncio.get_event_loop().time()
        time_since_activity = current_time - self._last_activity
        
        if time_since_activity > 600:
            self.log.info(f"HDFuryClient: Proactive reconnect after {time_since_activity:.0f}s inactivity")
            await self.disconnect()
        
        if not self.is_connected():
            await self.connect()

    def _get_command_timeout(self, command: str) -> float:
        if "set" in command:
            return 8.0
        else:
            return 5.0

    async def send_command(self, command: str, is_retry: bool = False) -> str:
        async with self._lock:
            try:
                await self._ensure_connection()
                
                timeout = self._get_command_timeout(command)
                
                self.log.debug(f"HDFuryClient: Sending command '{command}' (timeout: {timeout}s)")
                self._writer.write(f"{command}\r\n".encode('ascii'))
                await self._writer.drain()

                response = await asyncio.wait_for(self._reader.readline(), timeout=timeout)
                decoded = response.decode('ascii').replace('>', '').strip()
                self._last_activity = asyncio.get_event_loop().time()
                self.log.debug(f"HDFuryClient: Received response for '{command}': '{decoded}'")
                return decoded

            except asyncio.TimeoutError:
                self.log.warning(f"Command '{command}' timed out after {timeout}s - connection may be stale")
                await self.disconnect()
                
                if not is_retry:
                    self.log.info(f"Retrying command '{command}' after timeout")
                    return await self.send_command(command, is_retry=True)
                else:
                    self.log.error(f"Command '{command}' failed on retry after timeout")
                    raise asyncio.TimeoutError(f"Command '{command}' timed out on retry")

            except (ConnectionResetError, BrokenPipeError, ConnectionError, OSError) as e:
                await self.disconnect()
                if is_retry:
                    self.log.error(f"HDFuryClient: Command '{command}' failed on retry. Giving up. Error: {e}")
                    raise
                self.log.warning(f"HDFuryClient: Command '{command}' failed: {e}. Retrying once.")
                return await self.send_command(command, is_retry=True)

            except Exception as e:
                self.log.error(f"HDFuryClient: An unexpected error occurred for command '{command}': {e}", exc_info=True)
                await self.disconnect()
                raise

    # ===== SOURCE SWITCHING =====
    async def set_source(self, source: str):
        """Set input source."""
        formatted_source = format_source_for_command(source, self.model_config)
        if self.model_config.model_id == "vertex":
            await self.send_command(f"set input {formatted_source}")
        elif self.model_config.source_command:
            await self.send_command(f"set {self.model_config.source_command} {formatted_source}")

    # ===== MATRIX ROUTING (VERTEX/VERTEX2) =====
    async def route_matrix(self, output: str, source: str):
        """Route specific input to specific output (matrix switching)."""
        formatted_source = format_source_for_command(source, self.model_config)
        
        if self.model_config.model_id == "vertex":
            # VERTEX uses top/bot
            output_name = "top" if output == "tx0" else "bot"
            await self.send_command(f"set {output_name} {formatted_source}")
        else:
            # VERTEX2 uses inselTX0/inselTX1
            output_num = output.replace("tx", "")
            await self.send_command(f"set inseltx{output_num} {formatted_source}")

    # ===== EDID MANAGEMENT =====
    async def set_edid_mode(self, mode: str):
        """Set EDID mode."""
        await self.send_command(f"set edidmode {mode}")

    async def set_edid_audio(self, source: str):
        """Set EDID audio source."""
        await self.send_command(f"set edid audio {source}")

    async def load_edid_slot(self, slot: str):
        """Load EDID from slot."""
        await self.send_command(f"set edid load {slot}")

    async def save_edid_slot(self, slot: str):
        """Save current EDID to slot."""
        await self.send_command(f"set edid save {slot}")

    # ===== VIDEO SETTINGS =====
    async def set_color_space(self, mode: str):
        """Set color space mode."""
        mode_map = {
            "auto": "auto",
            "rgb": "rgb",
            "ycbcr444": "444",
            "ycbcr422": "422",
            "ycbcr420": "420"
        }
        await self.send_command(f"set colorspace {mode_map.get(mode, mode)}")

    async def set_deep_color(self, mode: str):
        """Set deep color bit depth."""
        mode_map = {
            "auto": "auto",
            "8bit": "8",
            "10bit": "10",
            "12bit": "12"
        }
        await self.send_command(f"set deepcolor {mode_map.get(mode, mode)}")

    async def set_output_resolution(self, resolution: str):
        """Set output resolution."""
        res_map = {
            "auto": "auto",
            "4k60": "2160p60",
            "4k30": "2160p30",
            "1080p60": "1080p60",
            "1080p30": "1080p30",
            "720p60": "720p60"
        }
        await self.send_command(f"set res {res_map.get(resolution, resolution)}")

    # ===== HDR CONTROL =====
    async def set_hdr_custom(self, state: bool):
        """Set custom HDR mode."""
        await self.send_command(f"set hdrcustom {'on' if state else 'off'}")

    async def set_hdr_disable(self, state: bool):
        """Disable HDR metadata."""
        await self.send_command(f"set hdrdisable {'on' if state else 'off'}")

    # ===== CEC & eARC =====
    async def set_cec(self, state: bool):
        """Enable/disable CEC engine."""
        await self.send_command(f"set cec {'on' if state else 'off'}")

    async def set_earc_force(self, mode: str):
        """Set eARC force mode."""
        await self.send_command(f"set earcforce {mode}")

    # ===== DISPLAY & SYSTEM =====
    async def set_oled(self, state: bool):
        """Enable/disable OLED display."""
        await self.send_command(f"set oled {'on' if state else 'off'}")

    async def set_autoswitch(self, state: bool):
        """Enable/disable automatic input switching."""
        await self.send_command(f"set autosw {'on' if state else 'off'}")

    async def set_hdcp_mode(self, mode: str):
        """Set HDCP mode."""
        if mode == "14":
            mode = "1.4"
        await self.send_command(f"set hdcp {mode}")

    # ===== SCALING =====
    async def set_scale_mode(self, mode: str):
        """Set video scaling mode."""
        if self.model_config.model_id == "arcana2":
            await self.send_command(f"set scalemode {mode}")
        else:
            await self.send_command(f"set scale {mode}")

    # ===== AUDIO =====
    async def set_audio_mode(self, mode: str):
        """Set audio routing mode (ARCANA2)."""
        await self.send_command(f"set audiomode {mode}")

    async def audio_delay_adjust(self, direction: int):
        """Adjust audio delay/lip sync (Maestro)."""
        if direction > 0:
            await self.send_command("set audiodelay +")
        else:
            await self.send_command("set audiodelay -")

    async def audio_delay_reset(self):
        """Reset audio delay to 0 (Maestro)."""
        await self.send_command("set audiodelay 0")

    # ===== LED CONTROL (DIVA) =====
    async def set_led_mode(self, mode: str):
        """Set LED/Ambilight mode (DIVA only)."""
        await self.send_command(f"set ledstyle {mode}")

    async def led_brightness_adjust(self, change: int):
        """Adjust LED brightness by relative amount (DIVA only)."""
        if change > 0:
            await self.send_command(f"set ledbright +{abs(change)}")
        else:
            await self.send_command(f"set ledbright -{abs(change)}")

    async def set_led_brightness(self, value: int):
        """Set LED brightness to absolute value 0-100 (DIVA only)."""
        value = max(0, min(100, value))
        await self.send_command(f"set ledbright {value}")

    # ===== DEVICE INFO =====
    async def get_firmware_version(self) -> str:
        """Get firmware version."""
        response = await self.send_command("get ver")
        return response

    async def get_device_info(self) -> str:
        """Get device information."""
        response = await self.send_command("get status")
        return response

    async def heartbeat(self) -> bool:
        """Check device connectivity."""
        try:
            if self.model_config.input_count > 0:
                await self.send_command("get insel")
            else:
                await self.send_command("get ver")
            return True
        except Exception as e:
            self.log.debug(f"Heartbeat failed: {e}")
            return False