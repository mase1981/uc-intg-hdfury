from __future__ import annotations
from typing import TYPE_CHECKING, Any
import logging
from ucapi import media_player, entity, api_definitions

if TYPE_CHECKING:
    from uc_intg_hdfury.device import HDFuryDevice

log = logging.getLogger(__name__)

class HDFuryMediaPlayer(media_player.MediaPlayer):
    def __init__(self, device: HDFuryDevice):
        self._device = device
        identifier = device.device_id
        
        features = []
        if device.model_config.input_count > 0:
            features.append(media_player.Features.SELECT_SOURCE)

        super().__init__(
            identifier=identifier,
            name=device.name,
            features=features,
            attributes={ 
                "state": media_player.States.UNAVAILABLE,
                "source_list": device.source_list,
                "source": None,
            },
            device_class=media_player.DeviceClasses.RECEIVER,
            cmd_handler=self.handle_command
        )

    async def handle_command(self, entity_arg: entity.Entity, command: str, kwargs: dict[str, Any]) -> api_definitions.StatusCodes:
        log.debug(f"HDFuryMediaPlayer received command: {command}")
        
        from uc_intg_hdfury.device import EVENTS
        
        try:
            if command == media_player.Commands.SELECT_SOURCE:
                source = kwargs.get("source")
                if source and source in self._device.source_list:
                    await self._device.client.set_source(source)
                    self._device.current_source = source
                    self._device.events.emit(EVENTS.UPDATE, self._device)
                    return api_definitions.StatusCodes.OK
                else:
                    log.warning(f"Invalid source requested: {source}")
                    return api_definitions.StatusCodes.BAD_REQUEST
                    
            elif command == media_player.Commands.PLAY_PAUSE:
                return api_definitions.StatusCodes.OK
            
            else:
                for source in self._device.source_list:
                    source_cmd = source.replace(" ", "_")
                    if command == source_cmd:
                        await self._device.client.set_source(source)
                        self._device.current_source = source
                        self._device.events.emit(EVENTS.UPDATE, self._device)
                        return api_definitions.StatusCodes.OK
                
                log.warning(f"Received unhandled command: {command}")
                return api_definitions.StatusCodes.NOT_IMPLEMENTED
        except Exception as e:
            log.error(f"Failed to execute command {command}: {e}")
            return api_definitions.StatusCodes.SERVER_ERROR