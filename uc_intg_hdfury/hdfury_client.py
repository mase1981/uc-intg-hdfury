import asyncio
import logging

class HDFuryClient:
    def __init__(self, host: str, port: int, log: logging.Logger):
        self.host, self.port, self.log = host, port, log
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()
        self._connection_lock = asyncio.Lock()
        self._last_activity = 0.0  # Track last successful command

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
        """
        Ensure connection is active, reconnect if needed.
        HDFury devices may drop inactive connections after ~10-15 minutes.
        """
        current_time = asyncio.get_event_loop().time()
        time_since_activity = current_time - self._last_activity
        
        # If more than 10 minutes since last activity, proactively reconnect
        if time_since_activity > 600:  # 10 minutes
            self.log.info(f"HDFuryClient: Proactive reconnect after {time_since_activity:.0f}s inactivity")
            await self.disconnect()
        
        if not self.is_connected():
            await self.connect()

    async def send_command(self, command: str, is_retry: bool = False) -> str:
        """
        Sends a command, reads the response to clear the buffer,
        and handles reconnects with enhanced timeout recovery.
        """
        async with self._lock:
            try:
                await self._ensure_connection()

                self.log.debug(f"HDFuryClient: Sending command '{command}'")
                self._writer.write(f"{command}\r\n".encode('ascii'))
                await self._writer.drain()

                response = await asyncio.wait_for(self._reader.readline(), timeout=5.0)  # Increased timeout
                decoded = response.decode('ascii').replace('>', '').strip()
                self._last_activity = asyncio.get_event_loop().time()  # Update activity timestamp
                self.log.debug(f"HDFuryClient: Received response for '{command}': '{decoded}'")
                return decoded

            except asyncio.TimeoutError:
                self.log.warning(f"Command '{command}' timed out - connection may be stale")
                await self.disconnect()  # Force disconnect on timeout
                
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

    async def get_device_name(self) -> str:
        return "VRRoom"

    async def get_source_list(self) -> list[str]:
        return ["HDMI 0", "HDMI 1", "HDMI 2", "HDMI 3"]

    async def get_current_source(self) -> str | None:
        response = await self.send_command("get insel")
        parts = response.split()
        if len(parts) >= 2 and parts[0] == "insel":
            return f"HDMI {int(parts[1])}"
        return None

    async def set_source(self, source: str):
        await self.send_command(f"set inseltx0 {source.replace('HDMI', '').strip()}")

    async def get_status(self, target: str) -> str:
        response = await self.send_command(f"get status {target}")
        prefix = f"get status {target}"
        return response[len(prefix):].strip() if response.startswith(prefix) else response
        
    async def set_output_power(self, output: int, state: bool):
        command = f"set tx{output}plus5 {'on' if state else 'off'}"
        await self.send_command(command)
    
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
        await self.send_command(f"set hdcp {mode}")

    async def heartbeat(self) -> bool:
        """
        Send a simple heartbeat command to keep connection alive.
        Returns True if successful, False if connection failed.
        """
        try:
            await self.send_command("get insel")
            return True
        except Exception as e:
            self.log.debug(f"Heartbeat failed: {e}")
            return False