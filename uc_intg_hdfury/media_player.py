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
        identifier = device.device_id  # Use shared device_id
        
        features = [
            media_player.Features.ON_OFF,
            media_player.Features.SELECT_SOURCE,
        ]

        super().__init__(
            identifier=identifier,
            name=device.name,
            features=features,
            attributes={ "state": media_player.States.UNAVAILABLE },
            device_class=media_player.DeviceClasses.RECEIVER,
            # REMOVED: device_id parameter - this was causing the error
            cmd_handler=self.handle_command
        )

    async def handle_command(self, entity_arg: entity.Entity, command: str, kwargs: dict[str, Any]) -> api_definitions.StatusCodes:
        log.debug(f"HDFuryMediaPlayer received command: {command}")
        
        try:
            if command == media_player.Commands.SELECT_SOURCE:
                source = kwargs.get("source")
                if source:
                    await self._device.client.set_source(source)
                    await self._device.start()
            elif command == media_player.Commands.ON:
                await self._device.set_power(True)
            elif command == media_player.Commands.OFF:
                await self._device.set_power(False)
            else:
                log.warning(f"Received unhandled command: {command}")
                return api_definitions.StatusCodes.NOT_IMPLEMENTED
        except Exception as e:
            log.error(f"Failed to execute command {command}: {e}")
            return api_definitions.StatusCodes.SERVER_ERROR
            
        return api_definitions.StatusCodes.OK