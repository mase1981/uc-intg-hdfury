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
        
        # REMOVED ON_OFF feature - HDFury devices don't have power commands
        # They are designed to stay powered on continuously
        features = [
            media_player.Features.SELECT_SOURCE,
        ]

        super().__init__(
            identifier=identifier,
            name=device.name,
            features=features,
            attributes={ 
                "state": media_player.States.UNAVAILABLE,
                "source_list": [],
                "source": None,
            },
            device_class=media_player.DeviceClasses.RECEIVER,
            cmd_handler=self.handle_command
        )

    async def handle_command(self, entity_arg: entity.Entity, command: str, kwargs: dict[str, Any]) -> api_definitions.StatusCodes:
        log.debug(f"HDFuryMediaPlayer received command: {command}")
        
        try:
            # REMOVED: ON/OFF commands - HDFury devices don't support power control
            if command == media_player.Commands.SELECT_SOURCE:
                source = kwargs.get("source")
                if source and source in self._device.source_list:
                    await self._device.client.set_source(source)
                    await self._device.start()  # Refresh state
                    return api_definitions.StatusCodes.OK
                else:
                    log.warning(f"Invalid source requested: {source}")
                    return api_definitions.StatusCodes.BAD_REQUEST
            elif command == media_player.Commands.PLAY_PAUSE:
                # No-op for HDFury devices - they don't have play/pause concept
                return api_definitions.StatusCodes.OK
            
            # Handle commands for activities (exposed as entity commands)
            # These are for direct source switching in activities
            elif command == "HDMI_0":
                await self._device.client.set_source("HDMI 0")
                await self._device.start()
                return api_definitions.StatusCodes.OK
            elif command == "HDMI_1":
                await self._device.client.set_source("HDMI 1")
                await self._device.start()
                return api_definitions.StatusCodes.OK
            elif command == "HDMI_2":
                await self._device.client.set_source("HDMI 2")
                await self._device.start()
                return api_definitions.StatusCodes.OK
            elif command == "HDMI_3":
                await self._device.client.set_source("HDMI 3")
                await self._device.start()
                return api_definitions.StatusCodes.OK
            else:
                log.warning(f"Received unhandled command: {command}")
                return api_definitions.StatusCodes.NOT_IMPLEMENTED
        except Exception as e:
            log.error(f"Failed to execute command {command}: {e}")
            return api_definitions.StatusCodes.SERVER_ERROR