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

    async def set_source(self, source: str):
        formatted_source = format_source_for_command(source, self.model_config)
        if self.model_config.model_id == "vertex":
            await self.send_command(f"set input {formatted_source}")
        elif self.model_config.source_command:
            await self.send_command(f"set {self.model_config.source_command} {formatted_source}")

    async def set_edid_mode(self, mode: str):
        await self.send_command(f"set edidmode {mode}")

    async def set_edid_audio(self, source: str):
        await self.send_command(f"set edid audio {source}")

    async def set_hdr_custom(self, state: bool):
        await self.send_command(f"set hdrcustom {'on' if state else 'off'}")

    async def set_hdr_disable(self, state: bool):
        await self.send_command(f"set hdrdisable {'on' if state else 'off'}")

    async def set_cec(self, state: bool):
        await self.send_command(f"set cec {'on' if state else 'off'}")

    async def set_earc_force(self, mode: str):
        await self.send_command(f"set earcforce {mode}")

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