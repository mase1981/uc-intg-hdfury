"""
HDFury Button entities.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from ucapi import StatusCodes
from ucapi.button import Attributes, Commands, States
from ucapi_framework import ButtonEntity

if TYPE_CHECKING:
    from uc_intg_hdfury.config import HDFuryConfig
    from uc_intg_hdfury.device import HDFuryDevice

_LOG = logging.getLogger(__name__)


class HDFuryButton(ButtonEntity):
    """Button that triggers a device action."""

    def __init__(
        self,
        entity_id: str,
        name: str,
        device: HDFuryDevice,
        action: Callable[[], Awaitable[bool]],
    ):
        self._device = device
        self._action = action
        super().__init__(entity_id, name, cmd_handler=self._handle_command)
        self.subscribe_to_device(device)

    async def sync_state(self):
        state = States.UNAVAILABLE if self._device.state == "UNAVAILABLE" else States.AVAILABLE
        self.update({Attributes.STATE: state})

    async def _handle_command(
        self, entity: Any, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id != Commands.PUSH:
            return StatusCodes.NOT_IMPLEMENTED
        _LOG.info("[%s] Button: %s", self._device.log_id, self.name)
        return StatusCodes.OK if await self._action() else StatusCodes.SERVER_ERROR


def create_buttons(config: HDFuryConfig, device: HDFuryDevice) -> list[HDFuryButton]:
    """Create button entities for HDFury device."""
    return [
        HDFuryButton(f"button.{config.identifier}.hotplug", f"{config.name} Hotplug", device, device.hotplug),
        HDFuryButton(f"button.{config.identifier}.reboot", f"{config.name} Reboot", device, device.reboot),
    ]
