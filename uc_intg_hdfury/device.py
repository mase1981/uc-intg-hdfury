import asyncio
import logging
from enum import IntEnum
from pyee.asyncio import AsyncIOEventEmitter
from uc_intg_hdfury.hdfury_client import HDFuryClient
from uc_intg_hdfury.media_player import HDFuryMediaPlayer
from uc_intg_hdfury.remote import HDFuryRemote
from ucapi import media_player, api_definitions

log = logging.getLogger(__name__)

class EVENTS(IntEnum):
    UPDATE = 1

class HDFuryDevice:
    def __init__(self, host: str, port: int, model: str | None = None):
        self.host, self.port = host, port
        self.client = HDFuryClient(host, port, log)
        self.events = AsyncIOEventEmitter()

        self.model: str = model or "HDFury"
        self.name: str = f"HDFury {self.model}"
        
        self.device_id = f"hdfury-{host.replace('.', '-')}" 
        
        self.state: media_player.States = media_player.States.UNAVAILABLE
        # Fixed source list - no need to poll device for this
        self.source_list: list[str] = ["HDMI 0", "HDMI 1", "HDMI 2", "HDMI 3"]
        self.current_source: str | None = None
        self.media_title: str | None = "Ready"
        self.media_artist: str | None = ""
        self.media_album: str | None = ""
        
        # Keep-alive tracking - simplified
        self._keep_alive_task: asyncio.Task | None = None
        self._last_successful_command: float = 0
        self._keep_alive_interval: int = 600  # 10 minutes - very infrequent
        
        # Command execution tracking
        self._command_in_progress: bool = False
        
        # Command queue and rate limiting for activities
        self._command_queue: asyncio.Queue = asyncio.Queue()
        self._command_processor_task: asyncio.Task | None = None
        self._last_command_time: float = 0
        self._min_command_interval: float = 0.5  # 500ms between commands
        
        self.media_player_entity = HDFuryMediaPlayer(self)
        self.remote_entity = HDFuryRemote(self)
        
    async def start(self):
        log.info(f"HDFuryDevice: Starting connection for {self.host}")
        
        # Start command processor if not already running
        if not self._command_processor_task or self._command_processor_task.done():
            self._command_processor_task = asyncio.create_task(self._process_command_queue())
        
        try:
            if not self.client.is_connected(): 
                await self.client.connect()
            
            # Minimal connection verification - just check if connection exists
            # Don't send any commands that could timeout
            if self.client.is_connected():
                # Device is connected - mark as available
                self.state = media_player.States.ON
                self.media_title = "Ready"
                self._last_successful_command = asyncio.get_event_loop().time()
                
                # Start keep-alive task if not already running
                if not self._keep_alive_task or self._keep_alive_task.done():
                    self._keep_alive_task = asyncio.create_task(self._keep_alive_loop())
            else:
                raise Exception("Failed to establish connection")

        except Exception as e:
            self.state = media_player.States.UNAVAILABLE
            self.media_title = "Connection Error"
            self.media_artist = ""
            self.media_album = ""
            log.error(f"HDFuryDevice connection error: {e}", exc_info=True)
        
        self.events.emit(EVENTS.UPDATE, self)

    async def stop(self):
        log.info(f"HDFuryDevice: Stopping connection to {self.host}")
        
        # Cancel command processor
        if self._command_processor_task and not self._command_processor_task.done():
            self._command_processor_task.cancel()
            try:
                await self._command_processor_task
            except asyncio.CancelledError:
                pass
        
        # Cancel keep-alive task
        if self._keep_alive_task and not self._keep_alive_task.done():
            self._keep_alive_task.cancel()
            try:
                await self._keep_alive_task
            except asyncio.CancelledError:
                pass
        
        if self.client.is_connected(): 
            await self.client.disconnect()
        self.state = media_player.States.UNAVAILABLE
        self.events.emit(EVENTS.UPDATE, self)

    async def _process_command_queue(self):
        """Process commands from queue with rate limiting to prevent device overload."""
        log.info(f"HDFuryDevice: Starting command processor for {self.host}")
        
        while True:
            try:
                # Get next command from queue
                command_data = await self._command_queue.get()
                
                if command_data is None:  # Shutdown signal
                    break
                
                command, future = command_data
                
                # Rate limiting: ensure minimum interval between commands
                current_time = asyncio.get_event_loop().time()
                time_since_last = current_time - self._last_command_time
                
                if time_since_last < self._min_command_interval:
                    sleep_time = self._min_command_interval - time_since_last
                    log.debug(f"Rate limiting: sleeping {sleep_time:.2f}s before command")
                    await asyncio.sleep(sleep_time)
                
                # Execute command
                try:
                    result = await self._execute_command_internal(command)
                    future.set_result(result)
                    self._last_command_time = asyncio.get_event_loop().time()
                    # Update successful command timestamp when commands work
                    if result == api_definitions.StatusCodes.OK:
                        self._last_successful_command = self._last_command_time
                except Exception as e:
                    future.set_exception(e)
                
                # Mark task as done
                self._command_queue.task_done()
                
            except asyncio.CancelledError:
                log.info(f"HDFuryDevice: Command processor cancelled for {self.host}")
                break
            except Exception as e:
                log.error(f"HDFuryDevice: Command processor error for {self.host}: {e}")

    async def _execute_command_internal(self, command: str):
        """Internal command execution with proper error handling."""
        log.debug(f"HDFuryDevice: Executing command '{command}'")
        
        try:
            if command.startswith("set_source_"):
                source = command.replace("set_source_", "").replace("_", " ")
                await self.client.set_source(source)
                # Update local state immediately
                self.current_source = source
                
            elif command.startswith("set_edidmode_"):
                mode = command.replace("set_edidmode_", "")
                await self.client.set_edid_mode(mode)
                
            elif command.startswith("set_edidaudio_"):
                source = command.replace("set_edidaudio_", "")
                if source == "51":
                    await self.client.set_edid_audio("5.1")
                else:
                    await self.client.set_edid_audio(source)
                    
            elif command.startswith("set_hdrcustom_"):
                state = (command == "set_hdrcustom_on")
                await self.client.set_hdr_custom(state)
                
            elif command.startswith("set_hdrdisable_"):
                state = (command == "set_hdrdisable_on")
                await self.client.set_hdr_disable(state)
                
            elif command.startswith("set_cec_"):
                state = (command == "set_cec_on")
                await self.client.set_cec(state)
                
            elif command.startswith("set_earcforce_"):
                mode = command.replace("set_earcforce_", "")
                await self.client.set_earc_force(mode)
                
            elif command.startswith("set_oled_"):
                state = (command == "set_oled_on")
                await self.client.set_oled(state)
                
            elif command.startswith("set_autosw_"):
                state = (command == "set_autosw_on")
                await self.client.set_autoswitch(state)
                
            elif command.startswith("set_hdcp_"):
                mode = command.replace("set_hdcp_", "")
                await self.client.set_hdcp_mode(mode)
                
            else:
                log.warning(f"Unsupported command: {command}")
                return api_definitions.StatusCodes.NOT_IMPLEMENTED
            
            return api_definitions.StatusCodes.OK
            
        except Exception as e:
            log.error(f"Error executing command '{command}': {e}", exc_info=True)
            return api_definitions.StatusCodes.SERVER_ERROR

    async def _queue_command(self, command: str) -> api_definitions.StatusCodes:
        """Queue a command for execution with proper rate limiting."""
        future = asyncio.Future()
        await self._command_queue.put((command, future))
        
        try:
            result = await asyncio.wait_for(future, timeout=10.0)
            return result
        except asyncio.TimeoutError:
            log.error(f"Command '{command}' timed out in queue")
            return api_definitions.StatusCodes.SERVER_ERROR

    async def _keep_alive_loop(self):
        """
        Minimal keep-alive that only checks connection health when needed.
        No status commands that could timeout.
        """
        log.info(f"HDFuryDevice: Starting keep-alive loop for {self.host}")
        
        while True:
            try:
                await asyncio.sleep(self._keep_alive_interval)
                
                # Skip heartbeat if command is in progress or queue is busy
                if self._command_in_progress or not self._command_queue.empty():
                    continue
                
                current_time = asyncio.get_event_loop().time()
                time_since_last_command = current_time - self._last_successful_command
                
                # Only check connection if it's been more than 20 minutes since last successful command
                if time_since_last_command > 1200:  # 20 minutes
                    log.debug(f"HDFuryDevice: Connection idle for {time_since_last_command:.0f}s, checking health")
                    
                    # Simple connection check - just verify socket is still open
                    if not self.client.is_connected():
                        log.warning(f"HDFuryDevice: Connection lost for {self.host}")
                        if self.state != media_player.States.UNAVAILABLE:
                            self.state = media_player.States.UNAVAILABLE
                            self.media_title = "Connection Lost"
                            self.events.emit(EVENTS.UPDATE, self)
                        
                        # Try to reconnect
                        try:
                            await self.client.connect()
                            if self.client.is_connected():
                                self.state = media_player.States.ON
                                self.media_title = "Ready"
                                self._last_successful_command = current_time
                                self.events.emit(EVENTS.UPDATE, self)
                                log.info(f"HDFuryDevice: Reconnected to {self.host}")
                        except Exception as e:
                            log.warning(f"HDFuryDevice: Reconnection failed for {self.host}: {e}")
                    
            except asyncio.CancelledError:
                log.info(f"HDFuryDevice: Keep-alive loop cancelled for {self.host}")
                break
            except Exception as e:
                log.error(f"HDFuryDevice: Keep-alive error for {self.host}: {e}")
                
                # Wait before retrying on error
                try:
                    await asyncio.sleep(60)  # Wait 1 minute before retry on error
                except asyncio.CancelledError:
                    break

    async def handle_remote_command(self, entity, cmd_id, kwargs):
        actual_cmd = kwargs.get("command")
        
        if not actual_cmd:
            log.error(f"HDFuryDevice received remote command without an actual command: {cmd_id}")
            return api_definitions.StatusCodes.BAD_REQUEST

        log.info(f"HDFuryDevice received remote command: {actual_cmd}")
        
        # Use the command queue for all commands to prevent overload
        result = await self._queue_command(actual_cmd)
        
        # Emit update event for UI refresh (lightweight)
        if result == api_definitions.StatusCodes.OK:
            self.events.emit(EVENTS.UPDATE, self)
        
        return result