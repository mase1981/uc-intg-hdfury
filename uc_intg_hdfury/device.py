"""
HDFury Integration for Unfolded Circle Remote Two/3.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""
import asyncio
import logging
from enum import IntEnum
from pyee.asyncio import AsyncIOEventEmitter
from uc_intg_hdfury.hdfury_client import HDFuryClient, HDFuryConnectionError, HDFuryCommandError
from uc_intg_hdfury.media_player import HDFuryMediaPlayer
from uc_intg_hdfury.remote import HDFuryRemote
from uc_intg_hdfury.models import ModelConfig, get_source_list
from ucapi import media_player, api_definitions

log = logging.getLogger(__name__)

class EVENTS(IntEnum):
    UPDATE = 1

class HDFuryDevice:
    def __init__(self, host: str, port: int, model_config: ModelConfig):
        self.host, self.port = host, port
        self.model_config = model_config
        self.client = HDFuryClient(host, port, log, model_config)
        self.events = AsyncIOEventEmitter()

        self.model: str = model_config.display_name
        self.name: str = f"HDFury {self.model}"
        
        self.device_id = f"hdfury-{host.replace('.', '-')}" 
        
        self.state: media_player.States = media_player.States.UNAVAILABLE
        self.source_list: list[str] = get_source_list(model_config)
        self.current_source: str | None = None
        self.media_title: str | None = "Ready"
        self.media_artist: str | None = ""
        self.media_album: str | None = ""
        
        self._keep_alive_task: asyncio.Task | None = None
        self._last_successful_command: float = 0
        self._keep_alive_interval: int = 600
        
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
            
            if self.client.is_connected():
                self.state = media_player.States.ON
                self.media_title = "Ready"
                self._last_successful_command = asyncio.get_event_loop().time()
                
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
        
        if self._command_processor_task and not self._command_processor_task.done():
            self._command_processor_task.cancel()
            try:
                await self._command_processor_task
            except asyncio.CancelledError:
                pass
        
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
                    if result == api_definitions.StatusCodes.OK:
                        self._last_successful_command = self._last_command_time
                except Exception as e:
                    future.set_exception(e)
                
                self._command_queue.task_done()
                
            except asyncio.CancelledError:
                log.info(f"HDFuryDevice: Command processor cancelled for {self.host}")
                break
            except Exception as e:
                log.error(f"HDFuryDevice: Command processor error for {self.host}: {e}")

    async def _execute_command_internal(self, command: str):
        log.info(f"HDFuryDevice: Executing command '{command}'")
        
        if not self.client.is_connected():
            log.error(f"HDFuryDevice: Cannot execute '{command}' - client not connected")
            return api_definitions.StatusCodes.SERVER_ERROR
        
        try:
            if command.startswith("set_source_"):
                source = command.replace("set_source_", "").replace("_", " ")
                await self.client.set_source(source)
                self.current_source = source
            
            elif command.startswith("route_tx"):
                parts = command.split("_", 2)
                if len(parts) >= 3:
                    output = parts[1]
                    source = parts[2].replace("_", " ")
                    await self.client.route_matrix(output, source)
            
            elif command.startswith("set_edidmode_"):
                mode = command.replace("set_edidmode_", "")
                await self.client.set_edid_mode(mode)
            
            elif command.startswith("set_edidaudio_"):
                source = command.replace("set_edidaudio_", "")
                if source == "51":
                    await self.client.set_edid_audio("5.1")
                else:
                    await self.client.set_edid_audio(source)
            
            elif command.startswith("load_edid_slot_"):
                slot = command.replace("load_edid_slot_", "")
                await self.client.load_edid_slot(slot)
            elif command.startswith("save_edid_slot_"):
                slot = command.replace("save_edid_slot_", "")
                await self.client.save_edid_slot(slot)
            
            elif command.startswith("set_colorspace_"):
                mode = command.replace("set_colorspace_", "")
                await self.client.set_color_space(mode)
            
            elif command.startswith("set_deepcolor_"):
                mode = command.replace("set_deepcolor_", "")
                await self.client.set_deep_color(mode)
            
            elif command.startswith("set_resolution_"):
                res = command.replace("set_resolution_", "")
                await self.client.set_output_resolution(res)
            
            elif command.startswith("set_hdrcustom_"):
                state = (command == "set_hdrcustom_on")
                await self.client.set_hdr_custom(state)
            
            elif command.startswith("set_hdrdisable_"):
                state = (command == "set_hdrdisable_on")
                await self.client.set_hdr_disable(state)
            
            elif command.startswith("set_cec_"):
                state = (command == "set_cec_on")
                await self.client.set_cec(state)
            
            elif command.startswith("set_arcforce_"):
                mode = command.replace("set_arcforce_", "")
                await self.client.set_arc_force(mode)
            
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
            
            elif command.startswith("set_scalemode_"):
                mode = command.replace("set_scalemode_", "")
                await self.client.set_scale_mode(mode)
            
            elif command.startswith("set_audiomode_"):
                mode = command.replace("set_audiomode_", "")
                await self.client.set_audio_mode(mode)
            
            elif command.startswith("set_ledprofilevideo_"):
                mode = command.replace("set_ledprofilevideo_", "")
                await self.client.set_ledprofilevideo_mode(mode)
            
            elif command.startswith("set_led_brightness_"):
                value = command.replace("set_led_brightness_", "")
                gain_map = {"25": 8, "50": 16, "75": 24, "100": 31}
                gain_value = gain_map.get(value, 16)
                await self.client.set_led_brightness(gain_value)
            
            elif command.startswith("mute_tx") and command.endswith("audio_on"):
                output = int(command.replace("mute_tx", "").replace("audio_on", ""))
                await self.client.mute_tx_audio(output, True)
            elif command.startswith("mute_tx") and command.endswith("audio_off"):
                output = int(command.replace("mute_tx", "").replace("audio_off", ""))
                await self.client.mute_tx_audio(output, False)

            elif command.startswith("set_analogvolume_"):
                value = int(command.replace("set_analogvolume_", ""))
                await self.client.set_analog_volume(value)
            elif command.startswith("set_analogbass_"):
                value = int(command.replace("set_analogbass_", ""))
                await self.client.set_analog_bass(value)
            elif command.startswith("set_analogtreble_"):
                value = int(command.replace("set_analogtreble_", ""))
                await self.client.set_analog_treble(value)

            elif command.startswith("set_tx") and command.endswith("plus5_on"):
                output = int(command.replace("set_tx", "").replace("plus5_on", ""))
                await self.client.set_tx_plus5(output, True)
            elif command.startswith("set_tx") and command.endswith("plus5_off"):
                output = int(command.replace("set_tx", "").replace("plus5_off", ""))
                await self.client.set_tx_plus5(output, False)

            elif command.startswith("set_htpcmode") and command.endswith("_on"):
                port = int(command.replace("set_htpcmode", "").replace("_on", ""))
                await self.client.set_htpc_mode(port, True)
            elif command.startswith("set_htpcmode") and command.endswith("_off"):
                port = int(command.replace("set_htpcmode", "").replace("_off", ""))
                await self.client.set_htpc_mode(port, False)

            elif command.startswith("set_oledpage_"):
                page = int(command.replace("set_oledpage_", ""))
                await self.client.set_oled_page(page)
            elif command.startswith("set_oledfade_"):
                seconds = int(command.replace("set_oledfade_", ""))
                await self.client.set_oled_fade(seconds)

            elif command.startswith("set_cecla_"):
                address = command.replace("set_cecla_", "")
                await self.client.set_cec_logical_address(address)

            elif command.startswith("set_avicustom_"):
                state = (command == "set_avicustom_on")
                await self.client.set_avi_custom(state)
            elif command.startswith("set_avidisable_"):
                state = (command == "set_avidisable_on")
                await self.client.set_avi_disable(state)

            elif command == "reboot_device":
                await self.client.reboot()
            elif command.startswith("factoryreset_"):
                mode = int(command.replace("factoryreset_", ""))
                await self.client.factory_reset(mode)
            elif command == "hotplug":
                await self.client.hotplug()

            elif command == "get_firmware_version":
                version = await self.client.get_firmware_version()
                log.info(f"Firmware version: {version}")
            elif command == "get_device_info":
                info = await self.client.get_device_info()
                log.info(f"Device info: {info}")

            else:
                log.warning(f"Unsupported command: {command}")
                return api_definitions.StatusCodes.NOT_IMPLEMENTED
            
            return api_definitions.StatusCodes.OK
            
        except Exception as e:
            log.error(f"Error executing command '{command}': {e}", exc_info=True)
            return api_definitions.StatusCodes.SERVER_ERROR

    async def _queue_command(self, command: str) -> api_definitions.StatusCodes:
        future = asyncio.Future()
        await self._command_queue.put((command, future))
        
        try:
            result = await asyncio.wait_for(future, timeout=10.0)
            return result
        except asyncio.TimeoutError:
            log.error(f"Command '{command}' timed out in queue")
            return api_definitions.StatusCodes.SERVER_ERROR

    async def _keep_alive_loop(self):
        log.info(f"HDFuryDevice: Starting keep-alive loop for {self.host}")
        retry_delays = [5, 10, 30, 60, 300]
        retry_attempt = 0

        while True:
            try:
                await asyncio.sleep(self._keep_alive_interval)

                if self._command_in_progress or not self._command_queue.empty():
                    continue

                current_time = asyncio.get_event_loop().time()
                time_since_last_command = current_time - self._last_successful_command

                if time_since_last_command > 1200:
                    log.debug(f"HDFuryDevice: Connection idle for {time_since_last_command:.0f}s, checking health")

                    if not self.client.is_connected():
                        log.warning(f"HDFuryDevice: Connection lost for {self.host}")
                        if self.state != media_player.States.UNAVAILABLE:
                            self.state = media_player.States.UNAVAILABLE
                            self.media_title = "Connection Lost"
                            self.events.emit(EVENTS.UPDATE, self)

                        retry_attempt = 0
                        while retry_attempt < len(retry_delays):
                            try:
                                delay = retry_delays[retry_attempt]
                                log.info(f"HDFuryDevice: Reconnection attempt {retry_attempt + 1}/{len(retry_delays)} for {self.host} (delay: {delay}s)")

                                await self.client.connect()
                                if self.client.is_connected():
                                    self.state = media_player.States.ON
                                    self.media_title = "Ready"
                                    self._last_successful_command = current_time
                                    self.events.emit(EVENTS.UPDATE, self)
                                    log.info(f"HDFuryDevice: Reconnected successfully to {self.host}")
                                    retry_attempt = 0
                                    break
                                else:
                                    raise HDFuryConnectionError("Connection failed")
                            except Exception as e:
                                log.warning(f"HDFuryDevice: Reconnection attempt {retry_attempt + 1} failed for {self.host}: {e}")
                                retry_attempt += 1

                                if retry_attempt < len(retry_delays):
                                    delay = retry_delays[retry_attempt - 1]
                                    log.info(f"HDFuryDevice: Waiting {delay}s before next attempt...")
                                    await asyncio.sleep(delay)
                                else:
                                    log.error(f"HDFuryDevice: All reconnection attempts exhausted for {self.host}")
                                    break
                    else:
                        retry_attempt = 0

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
        if kwargs is None:
            log.error(f"HDFuryDevice received command with None kwargs: {cmd_id}")
            return api_definitions.StatusCodes.BAD_REQUEST
            
        actual_cmd = kwargs.get("command")
        
        if not actual_cmd:
            log.error(f"HDFuryDevice received remote command without an actual command: {cmd_id}")
            return api_definitions.StatusCodes.BAD_REQUEST

        log.info(f"HDFuryDevice received remote command: {actual_cmd}")
        
        result = await self._queue_command(actual_cmd)
        
        if result == api_definitions.StatusCodes.OK:
            self.events.emit(EVENTS.UPDATE, self)
        
        return result