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
from uc_intg_hdfury.sensor import HDFurySensor
from uc_intg_hdfury.select_entities import HDFurySelectEntities
from uc_intg_hdfury.models import ModelConfig, get_source_list
from ucapi import media_player, api_definitions, select

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
        self.sensor_entities = HDFurySensor.create_sensors(self.device_id, self.name, model_config)
        self.select_entities = HDFurySelectEntities.create_select_entities(self)
        
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

                self._update_connection_sensor(True)

                asyncio.create_task(self._poll_initial_state())

                if not self._keep_alive_task or self._keep_alive_task.done():
                    self._keep_alive_task = asyncio.create_task(self._keep_alive_loop())
            else:
                raise Exception("Failed to establish connection")

        except Exception as e:
            self.state = media_player.States.UNAVAILABLE
            self.media_title = "Connection Error"
            self.media_artist = ""
            self.media_album = ""
            self._update_connection_sensor(False)
            log.error(f"HDFuryDevice connection error: {e}", exc_info=True)

        self.events.emit(EVENTS.UPDATE, self)

    async def _poll_initial_state(self):
        log.info(f"HDFuryDevice: Polling initial state for {self.host}")
        try:
            state = await self.client.poll_device_state()
            log.info(f"HDFuryDevice: Polled state: {state}")

            if "firmware" in state:
                self._update_firmware_sensor(state["firmware"])

            if "current_input" in state:
                input_num = state["current_input"]
                if input_num.isdigit():
                    input_idx = int(input_num)
                    if 0 <= input_idx < len(self.source_list):
                        self._update_input_sensor(self.source_list[input_idx])
                        self.current_source = self.source_list[input_idx]
                    else:
                        self._update_input_sensor(f"Input {input_num}")
                else:
                    self._update_input_sensor(input_num)

            if "edid_mode" in state:
                self._update_edid_mode_sensor(state["edid_mode"].title())

            if "hdr_mode" in state:
                self._update_hdr_mode_sensor(state["hdr_mode"])

            if "hdcp_mode" in state:
                self._update_hdcp_mode_sensor(state["hdcp_mode"])

            if "oled_status" in state:
                self._update_oled_status_sensor(state["oled_status"])

            if "autoswitch_status" in state:
                self._update_autoswitch_status_sensor(state["autoswitch_status"])

            if "audio_tx0" in state:
                self._update_audio_tx0_sensor(state["audio_tx0"])

            if "audio_tx1" in state:
                self._update_audio_tx1_sensor(state["audio_tx1"])

            if "audio_out" in state:
                self._update_audio_out_sensor(state["audio_out"])

            self.events.emit(EVENTS.UPDATE, self)

        except Exception as e:
            log.error(f"HDFuryDevice: Error polling initial state: {e}")

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
                self._update_input_sensor(source)
            
            elif command.startswith("route_tx"):
                parts = command.split("_", 2)
                if len(parts) >= 3:
                    output = parts[1]
                    source = parts[2].replace("_", " ")
                    await self.client.route_matrix(output, source)
            
            elif command.startswith("set_edidmode_"):
                mode = command.replace("set_edidmode_", "")
                await self.client.set_edid_mode(mode)
                self._update_edid_mode_sensor(mode.title())
            
            elif command.startswith("set_edidaudio_"):
                source = command.replace("set_edidaudio_", "")
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
                if state:
                    self._update_hdr_mode_sensor("Custom")

            elif command.startswith("set_hdrdisable_"):
                state = (command == "set_hdrdisable_on")
                await self.client.set_hdr_disable(state)
                if state:
                    self._update_hdr_mode_sensor("Disabled")
                else:
                    self._update_hdr_mode_sensor("Auto")
            
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
                self._update_oled_status_sensor(state)

            elif command.startswith("set_autosw_"):
                state = (command == "set_autosw_on")
                await self.client.set_autoswitch(state)
                self._update_autoswitch_status_sensor(state)
            
            elif command.startswith("set_hdcp_"):
                mode = command.replace("set_hdcp_", "")
                await self.client.set_hdcp_mode(mode)
                display_mode = "1.4" if mode == "14" else mode.upper()
                self._update_hdcp_mode_sensor(display_mode)
            
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
                                    self._update_connection_sensor(True)
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

    async def handle_select_command(self, entity, cmd_id, params, select_type: str):
        from ucapi.select import Commands, Attributes

        if cmd_id != Commands.SELECT_OPTION:
            log.warning(f"Unknown select command: {cmd_id}")
            return api_definitions.StatusCodes.NOT_IMPLEMENTED

        selected_option = params.get("option") if params else None
        if not selected_option:
            log.error(f"No option provided for select command")
            return api_definitions.StatusCodes.BAD_REQUEST

        log.info(f"HDFuryDevice: Select {select_type} -> {selected_option}")

        try:
            if select_type == "input":
                await self.client.set_source(selected_option)
                self.current_source = selected_option
                self._update_input_sensor(selected_option)

            elif select_type == "edid_mode":
                mode = selected_option.lower()
                await self.client.set_edid_mode(mode)
                self._update_edid_mode_sensor(selected_option)

            elif select_type == "edid_audio":
                audio_map = {"5.1": "51", "Stereo": "stereo", "Full": "full", "Audioout": "audioout", "Earcout": "earcout"}
                mode = audio_map.get(selected_option, selected_option.lower())
                await self.client.set_edid_audio(mode)

            elif select_type == "hdcp":
                hdcp_map = {"1.4": "14", "Auto": "auto", "2.2": "2.2"}
                mode = hdcp_map.get(selected_option, selected_option.lower())
                await self.client.set_hdcp_mode(mode)
                self._update_hdcp_mode_sensor(selected_option)

            elif select_type == "earcforce":
                earc_map = {
                    "Auto eARC": "autoearc",
                    "Manual eARC": "manualearc",
                    "Manual HDMI": "hdmi",
                    "Auto ARC": "autoarc",
                    "Manual ARC": "manualarc",
                }
                mode = earc_map.get(selected_option, selected_option.lower())
                await self.client.set_earc_force(mode)

            elif select_type == "arcforce":
                mode = selected_option.lower()
                await self.client.set_arc_force(mode)

            elif select_type == "hdr":
                if selected_option == "Auto":
                    await self.client.set_hdr_custom(False)
                    await self.client.set_hdr_disable(False)
                elif selected_option == "Custom":
                    await self.client.set_hdr_disable(False)
                    await self.client.set_hdr_custom(True)
                elif selected_option == "Disabled":
                    await self.client.set_hdr_custom(False)
                    await self.client.set_hdr_disable(True)
                self._update_hdr_mode_sensor(selected_option)

            elif select_type == "cecla":
                mode = selected_option.lower()
                await self.client.set_cec_logical_address(mode)

            else:
                log.warning(f"Unknown select type: {select_type}")
                return api_definitions.StatusCodes.NOT_IMPLEMENTED

            entity.attributes[Attributes.CURRENT_OPTION] = selected_option
            self.events.emit(EVENTS.UPDATE, self)
            return api_definitions.StatusCodes.OK

        except Exception as e:
            log.error(f"Error executing select command {select_type} -> {selected_option}: {e}")
            return api_definitions.StatusCodes.SERVER_ERROR

    def _get_sensor_by_id_suffix(self, suffix: str):
        """Get sensor entity by ID suffix."""
        target_id = f"{self.device_id}-{suffix}"
        for sensor in self.sensor_entities:
            if sensor.id == target_id:
                return sensor
        return None

    def _update_connection_sensor(self, connected: bool):
        """Update connection sensor."""
        if sensor := self._get_sensor_by_id_suffix("connection"):
            HDFurySensor.update_connection_sensor(sensor, connected)

    def _update_firmware_sensor(self, version: str):
        """Update firmware sensor."""
        if sensor := self._get_sensor_by_id_suffix("firmware"):
            HDFurySensor.update_firmware_sensor(sensor, version)

    def _update_input_sensor(self, input_name: str):
        """Update current input sensor."""
        if sensor := self._get_sensor_by_id_suffix("current-input"):
            HDFurySensor.update_input_sensor(sensor, input_name)

    def _update_edid_mode_sensor(self, mode: str):
        """Update EDID mode sensor."""
        if sensor := self._get_sensor_by_id_suffix("edid-mode"):
            HDFurySensor.update_edid_mode_sensor(sensor, mode)

    def _update_hdr_mode_sensor(self, mode: str):
        """Update HDR mode sensor."""
        if sensor := self._get_sensor_by_id_suffix("hdr-mode"):
            HDFurySensor.update_hdr_mode_sensor(sensor, mode)

    def _update_hdcp_mode_sensor(self, mode: str):
        """Update HDCP mode sensor."""
        if sensor := self._get_sensor_by_id_suffix("hdcp-mode"):
            HDFurySensor.update_hdcp_mode_sensor(sensor, mode)

    def _update_oled_status_sensor(self, enabled: bool):
        """Update OLED status sensor."""
        if sensor := self._get_sensor_by_id_suffix("oled-status"):
            HDFurySensor.update_oled_status_sensor(sensor, enabled)

    def _update_autoswitch_status_sensor(self, enabled: bool):
        """Update autoswitch status sensor."""
        if sensor := self._get_sensor_by_id_suffix("autoswitch-status"):
            HDFurySensor.update_autoswitch_status_sensor(sensor, enabled)

    def _update_colorspace_sensor(self, mode: str):
        """Update color space sensor."""
        if sensor := self._get_sensor_by_id_suffix("colorspace"):
            HDFurySensor.update_colorspace_sensor(sensor, mode)

    def _update_deep_color_sensor(self, mode: str):
        """Update deep color sensor."""
        if sensor := self._get_sensor_by_id_suffix("deep-color"):
            HDFurySensor.update_deep_color_sensor(sensor, mode)

    def _update_audio_tx0_sensor(self, audio_info: str):
        """Update audio TX0 sensor."""
        if sensor := self._get_sensor_by_id_suffix("audio-tx0"):
            HDFurySensor.update_audio_tx0_sensor(sensor, audio_info)

    def _update_audio_tx1_sensor(self, audio_info: str):
        """Update audio TX1 sensor."""
        if sensor := self._get_sensor_by_id_suffix("audio-tx1"):
            HDFurySensor.update_audio_tx1_sensor(sensor, audio_info)

    def _update_audio_out_sensor(self, audio_info: str):
        """Update audio out sensor."""
        if sensor := self._get_sensor_by_id_suffix("audio-out"):
            HDFurySensor.update_audio_out_sensor(sensor, audio_info)