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
        
        self.state: media_player.States = media_player.States.UNAVAILABLE
        self.source_list: list[str] = []
        self.current_source: str | None = None
        self.media_title: str | None = "Offline"
        self.media_artist: str | None = ""
        self.media_album: str | None = ""
        
        self.media_player_entity = HDFuryMediaPlayer(self)
        self.remote_entity = HDFuryRemote(self)
        
    async def start(self):
        log.info(f"HDFuryDevice: Starting poll for {self.host}")
        try:
            if not self.client.is_connected(): await self.client.connect()
            
            results = await asyncio.gather(
                self.client.get_source_list(),
                self.client.get_current_source(), 
                self.client.get_status("rx0"),
                self.client.get_status("tx0"),
                self.client.get_status("tx0sink")
            )
            self.source_list, self.current_source, self.media_title, self.media_artist, self.media_album = results
            
            self.state = media_player.States.ON

        except Exception as e:
            self.state = media_player.States.UNAVAILABLE
            self.media_title = "Offline"
            self.media_artist = ""
            self.media_album = ""
            log.error(f"HDFuryDevice connection error: {e}", exc_info=True)
        
        self.events.emit(EVENTS.UPDATE, self)

    async def stop(self):
        log.info(f"HDFuryDevice: Stopping connection to {self.host}")
        if self.client.is_connected(): await self.client.disconnect()
        self.state = media_player.States.OFF
        self.events.emit(EVENTS.UPDATE, self)

    async def set_power(self, state: bool):
        log.info(f"Setting TX0 power to {'ON' if state else 'OFF'}")
        try:
            await self.client.set_output_power(0, state)
            await asyncio.sleep(1)
            self.state = media_player.States.ON if state else media_player.States.OFF
            self.events.emit(EVENTS.UPDATE, self)
        except Exception as e:
            log.error(f"Failed to set power: {e}")
            self.state = media_player.States.UNAVAILABLE
            self.events.emit(EVENTS.UPDATE, self)
    
    async def handle_remote_command(self, entity, cmd_id, kwargs):
        actual_cmd = kwargs.get("command")
        
        if not actual_cmd:
            log.error(f"HDFuryDevice received remote command without an actual command: {cmd_id}")
            return api_definitions.StatusCodes.BAD_REQUEST

        log.info(f"HDFuryDevice received remote command: {actual_cmd}")
        
        try:
            if actual_cmd.startswith("set_source_"):
                source = actual_cmd.replace("set_source_", "").replace("_", " ")
                await self.client.set_source(source)
            elif actual_cmd.startswith("set_edidmode_"):
                mode = actual_cmd.replace("set_edidmode_", "")
                await self.client.set_edid_mode(mode)
            elif actual_cmd.startswith("set_edidaudio_"):
                source = actual_cmd.replace("set_edidaudio_", "")
                if source == "51":
                    await self.client.set_edid_audio("5.1")
                else:
                    await self.client.set_edid_audio(source)
            elif actual_cmd.startswith("set_hdrcustom_"):
                state = (actual_cmd == "set_hdrcustom_on")
                await self.client.set_hdr_custom(state)
            elif actual_cmd.startswith("set_hdrdisable_"):
                state = (actual_cmd == "set_hdrdisable_on")
                await self.client.set_hdr_disable(state)
            elif actual_cmd.startswith("set_cec_"):
                state = (actual_cmd == "set_cec_on")
                await self.client.set_cec(state)
            elif actual_cmd.startswith("set_earcforce_"):
                mode = actual_cmd.replace("set_earcforce_", "")
                await self.client.set_earc_force(mode)
            elif actual_cmd.startswith("set_oled_"):
                state = (actual_cmd == "set_oled_on")
                await self.client.set_oled(state)
            elif actual_cmd.startswith("set_autosw_"):
                state = (actual_cmd == "set_autosw_on")
                await self.client.set_autoswitch(state)
            elif actual_cmd.startswith("set_hdcp_"):
                mode = actual_cmd.replace("set_hdcp_", "")
                await self.client.set_hdcp_mode(mode)
            else:
                log.warning(f"Unsupported command: {actual_cmd}")
                return api_definitions.StatusCodes.NOT_IMPLEMENTED
            
            await self.start()
        except Exception as e:
            log.error(f"Error executing remote command '{actual_cmd}': {e}", exc_info=True)
            return api_definitions.StatusCodes.SERVER_ERROR

        return api_definitions.StatusCodes.OK