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
        self.source_list: list[str] = ["HDMI 0", "HDMI 1", "HDMI 2", "HDMI 3"]
        self.current_source: str | None = None
        self.media_title: str | None = "Offline"
        self.media_artist: str | None = ""
        self.media_album: str | None = ""
        
        self._keep_alive_task: asyncio.Task | None = None
        self._last_successful_poll: float = 0
        self._keep_alive_interval: int = 300
        
        self._command_in_progress: bool = False
        
        self._command_queue: asyncio.Queue = asyncio.Queue()
        self._command_processor_task: asyncio.Task | None = None
        self._last_command_time: float = 0
        self._min_command_interval: float = 0.5
        
        self.media_player_entity = HDFuryMediaPlayer(self)
        self.remote_entity = HDFuryRemote(self)
        
    async def start(self):
        log.info(f"HDFuryDevice: Starting connection for {self.host}")
        
        if not self._command_processor_task or self._command_processor_task.done():
            self._command_processor_task = asyncio.create_task(self._process_command_queue())
        
        try:
            if not self.client.is_connected(): 
                await self.client.connect()
            

            test_response = await self.client.send_command("get version")
            if test_response:
                self.state = media_player.States.ON
                self._last_successful_poll = asyncio.get_event_loop().time()
                
                if not self._keep_alive_task or self._keep_alive_task.done():
                    self._keep_alive_task = asyncio.create_task(self._keep_alive_loop())
            else:
                raise Exception("Device not responding to version command")

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
                command_data = await self._command_queue.get()
                
                if command_data is None:
                    break
                
                command, future = command_data
                
                current_time = asyncio.get_event_loop().time()
                time_since_last = current_time - self._last_command_time
                
                if time_since_last < self._min_command_interval:
                    sleep_time = self._min_command_interval - time_since_last
                    log.debug(f"Rate limiting: sleeping {sleep_time:.2f}s before command")
                    await asyncio.sleep(sleep_time)
                
                try:
                    result = await self._execute_command_internal(command)
                    future.set_result(result)
                    self._last_command_time = asyncio.get_event_loop().time()
                except Exception as e:
                    future.set_exception(e)
                
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
                self._last_successful_poll = asyncio.get_event_loop().time()
                
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
        Simplified keep-alive that just maintains connection without polling status.
        """
        log.info(f"HDFuryDevice: Starting keep-alive loop for {self.host}")
        
        while True:
            try:
                await asyncio.sleep(self._keep_alive_interval)
                
                # Skip heartbeat if command is in progress or queue is busy
                if self._command_in_progress or not self._command_queue.empty():
                    log.debug(f"HDFuryDevice: Skipping heartbeat - commands in progress")
                    continue
                
                current_time = asyncio.get_event_loop().time()
                time_since_last_poll = current_time - self._last_successful_poll
                
                if time_since_last_poll > 600:  # 10 minutes
                    log.debug(f"HDFuryDevice: Checking connection health for {self.host}")
                    
                    try:
                        test_response = await asyncio.wait_for(
                            self.client.send_command("get version"), timeout=3.0
                        )
                        if test_response:
                            self._last_successful_poll = current_time
                            # Update state if we were previously unavailable
                            if self.state == media_player.States.UNAVAILABLE:
                                log.info(f"HDFuryDevice: Device {self.host} back online")
                                self.state = media_player.States.ON
                                self.events.emit(EVENTS.UPDATE, self)
                        else:
                            raise Exception("No response to version command")
                    except Exception as e:
                        log.warning(f"HDFuryDevice: Connection check failed for {self.host}: {e}")
                        if self.state != media_player.States.UNAVAILABLE:
                            self.state = media_player.States.UNAVAILABLE
                            self.media_title = "Connection Lost"
                            self.events.emit(EVENTS.UPDATE, self)
                    
            except asyncio.CancelledError:
                log.info(f"HDFuryDevice: Keep-alive loop cancelled for {self.host}")
                break
            except Exception as e:
                log.error(f"HDFuryDevice: Keep-alive error for {self.host}: {e}")
                
                try:
                    await asyncio.sleep(60)
                except asyncio.CancelledError:
                    break

    async def handle_remote_command(self, entity, cmd_id, kwargs):
        actual_cmd = kwargs.get("command")
        
        if not actual_cmd:
            log.error(f"HDFuryDevice received remote command without an actual command: {cmd_id}")
            return api_definitions.StatusCodes.BAD_REQUEST

        log.info(f"HDFuryDevice received remote command: {actual_cmd}")
        
        result = await self._queue_command(actual_cmd)
        
        if result == api_definitions.StatusCodes.OK:
            self.events.emit(EVENTS.UPDATE, self)
        
        return result