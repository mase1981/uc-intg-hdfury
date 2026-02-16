"""
HDFury Integration for Unfolded Circle Remote Two/3.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""
import asyncio
import logging
from uc_intg_hdfury.models import ModelConfig, format_source_for_command


class HDFuryConnectionError(Exception):
    """Connection-related error."""
    pass


class HDFuryCommandError(Exception):
    """Command execution error."""
    pass

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

    async def send_command(self, command: str, is_retry: bool = False, expect_response: bool = True) -> str:
        async with self._lock:
            try:
                await self._ensure_connection()

                timeout = self._get_command_timeout(command)

                self.log.info(f"HDFuryClient: Sending command '{command}' (timeout: {timeout}s)")
                self._writer.write(f"{command}\r\n".encode('ascii'))
                await self._writer.drain()

                try:
                    response = await asyncio.wait_for(self._reader.readline(), timeout=timeout)
                    decoded = response.decode('ascii').replace('>', '').strip()
                    self._last_activity = asyncio.get_event_loop().time()
                    self.log.info(f"HDFuryClient: Received response for '{command}': '{decoded}'")
                    return decoded
                except asyncio.TimeoutError:
                    if command.startswith("set "):
                        self.log.debug(f"HDFuryClient: Command '{command}' completed without response (normal for some SET commands)")
                        self._last_activity = asyncio.get_event_loop().time()
                        return ""
                    elif not expect_response:
                        self.log.debug(f"HDFuryClient: Command '{command}' completed without response")
                        self._last_activity = asyncio.get_event_loop().time()
                        return ""
                    else:
                        raise

            except asyncio.TimeoutError:
                self.log.warning(f"Command '{command}' timed out after {timeout}s - connection may be stale")
                await self.disconnect()

                if not is_retry:
                    self.log.info(f"Retrying command '{command}' after timeout")
                    return await self.send_command(command, is_retry=True, expect_response=expect_response)
                else:
                    self.log.error(f"Command '{command}' failed on retry after timeout")
                    raise asyncio.TimeoutError(f"Command '{command}' timed out on retry")

            except (ConnectionResetError, BrokenPipeError, ConnectionError, OSError) as e:
                await self.disconnect()
                if is_retry:
                    self.log.error(f"HDFuryClient: Command '{command}' failed on retry. Giving up. Error: {e}")
                    raise
                self.log.warning(f"HDFuryClient: Command '{command}' failed: {e}. Retrying once.")
                return await self.send_command(command, is_retry=True, expect_response=expect_response)

            except Exception as e:
                self.log.error(f"HDFuryClient: An unexpected error occurred for command '{command}': {e}", exc_info=True)
                await self.disconnect()
                raise

    async def set_source(self, source: str):
        formatted_source = format_source_for_command(source, self.model_config)
        if self.model_config.model_id == "vertex":
            await self.send_command(f"set input {formatted_source}")
        elif self.model_config.source_command:
            await self.send_command(f"set {self.model_config.source_command} {formatted_source}")

    async def route_matrix(self, output: str, source: str):
        formatted_source = format_source_for_command(source, self.model_config)
        
        if self.model_config.model_id == "vertex":
            output_name = "top" if output == "tx0" else "bot"
            await self.send_command(f"set {output_name} {formatted_source}")
        else:
            output_num = output.replace("tx", "")
            await self.send_command(f"set inseltx{output_num} {formatted_source}")

    async def set_edid_mode(self, mode: str):
        await self.send_command(f"set edidmode {mode}")

    async def set_edid_audio(self, source: str):
        await self.send_command(f"set edid audio {source}")

    async def load_edid_slot(self, slot: str):
        await self.send_command(f"set edid load {slot}")

    async def save_edid_slot(self, slot: str):
        await self.send_command(f"set edid save {slot}")

    async def set_color_space(self, mode: str):
        mode_map = {
            "auto": "auto",
            "rgb": "rgb",
            "ycbcr444": "444",
            "ycbcr422": "422",
            "ycbcr420": "420"
        }
        await self.send_command(f"set colorspace {mode_map.get(mode, mode)}")

    async def set_deep_color(self, mode: str):
        mode_map = {
            "auto": "auto",
            "8bit": "8",
            "10bit": "10",
            "12bit": "12"
        }
        await self.send_command(f"set deepcolor {mode_map.get(mode, mode)}")

    async def set_output_resolution(self, resolution: str):
        res_map = {
            "auto": "auto",
            "4k60": "2160p60",
            "4k30": "2160p30",
            "1080p60": "1080p60",
            "1080p30": "1080p30",
            "720p60": "720p60"
        }
        await self.send_command(f"set res {res_map.get(resolution, resolution)}")

    async def set_hdr_custom(self, state: bool):
        await self.send_command(f"set hdrcustom {'on' if state else 'off'}")

    async def set_hdr_disable(self, state: bool):
        await self.send_command(f"set hdrdisable {'on' if state else 'off'}")

    async def set_cec(self, state: bool):
        await self.send_command(f"set cec {'on' if state else 'off'}")

    async def set_arc_force(self, mode: str):
        await self.send_command(f"set arcforce {mode}", expect_response=False)

    async def set_earc_force(self, mode: str):
        await self.send_command(f"set earcforce {mode}", expect_response=False)

    async def set_oled(self, state: bool):
        await self.send_command(f"set oled {'on' if state else 'off'}")

    async def set_autoswitch(self, state: bool):
        await self.send_command(f"set autosw {'on' if state else 'off'}")

    async def set_hdcp_mode(self, mode: str):
        if mode == "14":
            mode = "1.4"
        await self.send_command(f"set hdcp {mode}")

    async def set_scale_mode(self, mode: str):
        if self.model_config.model_id == "arcana2":
            await self.send_command(f"set scalemode {mode}")
        else:
            await self.send_command(f"set scale {mode}")

    async def set_audio_mode(self, mode: str):
        await self.send_command(f"set audiomode {mode}")

    async def set_ledprofilevideo_mode(self, mode: str):
        await self.send_command(f"set ledprofilevideo {mode}")

    async def set_led_brightness(self, value: int):
        value = max(0, min(31, value))
        await self.send_command(f"set ledredgain {value}")
        await self.send_command(f"set ledgreengain {value}")
        await self.send_command(f"set ledbluegain {value}")

    async def mute_tx_audio(self, output: int, state: bool):
        await self.send_command(f"set mutetx{output}audio {'on' if state else 'off'}")

    async def set_analog_volume(self, value: int):
        value = max(-30, min(10, value))
        await self.send_command(f"set analogvolume {value}")

    async def set_analog_bass(self, value: int):
        value = max(-10, min(10, value))
        await self.send_command(f"set analogbass {value}")

    async def set_analog_treble(self, value: int):
        value = max(-10, min(10, value))
        await self.send_command(f"set analogtreble {value}")

    async def set_tx_plus5(self, output: int, state: bool):
        await self.send_command(f"set tx{output}plus5 {'on' if state else 'off'}")

    async def set_htpc_mode(self, port: int, state: bool):
        await self.send_command(f"set htpcmode{port} {'on' if state else 'off'}")

    async def set_oled_page(self, page: int):
        page = max(0, min(4, page))
        await self.send_command(f"set oledpage {page}")

    async def set_oled_fade(self, seconds: int):
        seconds = max(0, min(255, seconds))
        await self.send_command(f"set oledfade {seconds}")

    async def set_cec_logical_address(self, address: str):
        if address in ["video", "audio"]:
            await self.send_command(f"set cecla {address}")

    async def set_avi_custom(self, state: bool):
        await self.send_command(f"set avicustom {'on' if state else 'off'}")

    async def set_avi_disable(self, state: bool):
        await self.send_command(f"set avidisable {'on' if state else 'off'}")

    async def reboot(self):
        await self.send_command("set reboot")

    async def factory_reset(self, mode: int):
        if mode in [1, 2, 3]:
            await self.send_command(f"set factoryreset {mode}")
        else:
            raise HDFuryCommandError(f"Invalid factory reset mode: {mode}. Must be 1, 2, or 3.")

    async def hotplug(self):
        await self.send_command("set hotplug")

    async def get_firmware_version(self) -> str:
        response = await self.send_command("get ver")
        return response

    async def get_device_info(self) -> str:
        response = await self.send_command("get status rx0")
        return response

    async def heartbeat(self) -> bool:
        try:
            if self.model_config.input_count > 0:
                await self.send_command("get insel")
            else:
                await self.send_command("get ver")
            return True
        except Exception as e:
            self.log.debug(f"Heartbeat failed: {e}")
            return False

    async def get_current_input(self) -> str | None:
        try:
            response = await self.send_command("get insel")
            if response and "insel" in response:
                parts = response.split()
                if len(parts) >= 2:
                    return parts[1]
            return None
        except Exception as e:
            self.log.debug(f"Failed to get current input: {e}")
            return None

    async def get_edid_mode(self) -> str | None:
        try:
            response = await self.send_command("get edidmode")
            if response and "edidmode" in response:
                parts = response.split()
                if len(parts) >= 2:
                    return parts[1]
            return None
        except Exception as e:
            self.log.debug(f"Failed to get EDID mode: {e}")
            return None

    async def get_hdr_mode(self) -> str | None:
        try:
            hdrcustom = await self.send_command("get hdrcustom")
            hdrdisable = await self.send_command("get hdrdisable")

            custom_on = hdrcustom and "on" in hdrcustom.lower()
            disable_on = hdrdisable and "on" in hdrdisable.lower()

            if disable_on:
                return "Disabled"
            elif custom_on:
                return "Custom"
            else:
                return "Auto"
        except Exception as e:
            self.log.debug(f"Failed to get HDR mode: {e}")
            return None

    async def get_hdcp_mode(self) -> str | None:
        try:
            response = await self.send_command("get hdcp")
            if response and "hdcp" in response:
                parts = response.split()
                if len(parts) >= 2:
                    return parts[1].upper()
            return None
        except Exception as e:
            self.log.debug(f"Failed to get HDCP mode: {e}")
            return None

    async def get_oled_status(self) -> bool | None:
        try:
            response = await self.send_command("get oled")
            if response and "oled" in response:
                return "on" in response.lower()
            return None
        except Exception as e:
            self.log.debug(f"Failed to get OLED status: {e}")
            return None

    async def get_autoswitch_status(self) -> bool | None:
        try:
            response = await self.send_command("get autosw")
            if response and "autosw" in response:
                return "on" in response.lower()
            return None
        except Exception as e:
            self.log.debug(f"Failed to get autoswitch status: {e}")
            return None

    async def get_earcforce_mode(self) -> str | None:
        try:
            response = await self.send_command("get earcforce")
            if response and "earcforce" in response:
                parts = response.split()
                if len(parts) >= 2:
                    return parts[1].upper()
            return None
        except Exception as e:
            self.log.debug(f"Failed to get eARC force mode: {e}")
            return None

    async def get_audio_tx0(self) -> str | None:
        try:
            mode_resp = await self.send_command("get audiomodetx0")
            mode = "Unknown"
            if mode_resp and "audiomodetx0" in mode_resp:
                parts = mode_resp.split(None, 1)
                if len(parts) >= 2:
                    mode = parts[1]

            status_resp = await self.send_command("get status aud0")
            if status_resp and "AUD0:" in status_resp:
                audio_info = status_resp.replace("AUD0:", "").strip()
                if audio_info:
                    return audio_info
            return mode
        except Exception as e:
            self.log.debug(f"Failed to get audio TX0: {e}")
            return None

    async def get_audio_tx1(self) -> str | None:
        try:
            mode_resp = await self.send_command("get audiomodetx1")
            mode = "Unknown"
            if mode_resp and "audiomodetx1" in mode_resp:
                parts = mode_resp.split(None, 1)
                if len(parts) >= 2:
                    mode = parts[1]

            status_resp = await self.send_command("get status aud1")
            if status_resp and "AUD1:" in status_resp:
                audio_info = status_resp.replace("AUD1:", "").strip()
                if audio_info:
                    return audio_info
            return mode
        except Exception as e:
            self.log.debug(f"Failed to get audio TX1: {e}")
            return None

    async def get_audio_out(self) -> str | None:
        try:
            response = await self.send_command("get status audout")
            if response and "AUDOUT:" in response:
                audio_info = response.replace("AUDOUT:", "").strip()
                if audio_info:
                    return audio_info
            return "No signal"
        except Exception as e:
            self.log.debug(f"Failed to get audio out: {e}")
            return None

    async def poll_device_state(self) -> dict:
        state = {}
        try:
            ver = await self.send_command("get ver")
            if ver and "ver" in ver:
                parts = ver.split()
                if len(parts) >= 2:
                    state["firmware"] = parts[1]

            if self.model_config.input_count > 0:
                input_val = await self.get_current_input()
                if input_val is not None:
                    state["current_input"] = input_val

            if len(self.model_config.edid_modes) > 0:
                edid = await self.get_edid_mode()
                if edid:
                    state["edid_mode"] = edid

            if self.model_config.hdr_custom_support or self.model_config.hdr_disable_support:
                hdr = await self.get_hdr_mode()
                if hdr:
                    state["hdr_mode"] = hdr

            if self.model_config.hdcp_modes:
                hdcp = await self.get_hdcp_mode()
                if hdcp:
                    state["hdcp_mode"] = hdcp

            if self.model_config.oled_support:
                oled = await self.get_oled_status()
                if oled is not None:
                    state["oled_status"] = oled

            if self.model_config.autoswitch_support:
                autosw = await self.get_autoswitch_status()
                if autosw is not None:
                    state["autoswitch_status"] = autosw

            if self.model_config.matrix_outputs and self.model_config.matrix_outputs >= 1:
                audio_tx0 = await self.get_audio_tx0()
                if audio_tx0:
                    state["audio_tx0"] = audio_tx0

            if self.model_config.matrix_outputs and self.model_config.matrix_outputs >= 2:
                audio_tx1 = await self.get_audio_tx1()
                if audio_tx1:
                    state["audio_tx1"] = audio_tx1

            if self.model_config.model_id in ["vrroom", "vertex2", "vertex", "diva", "maestro"]:
                audio_out = await self.get_audio_out()
                if audio_out:
                    state["audio_out"] = audio_out

        except Exception as e:
            self.log.error(f"Error polling device state: {e}")

        return state