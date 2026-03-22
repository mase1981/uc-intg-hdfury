"""
HDFury Select entities.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from ucapi import StatusCodes
from ucapi.select import Attributes, Commands, States
from ucapi_framework import SelectEntity

if TYPE_CHECKING:
    from uc_intg_hdfury.config import HDFuryConfig
    from uc_intg_hdfury.device import HDFuryDevice

_LOG = logging.getLogger(__name__)


class HDFurySelect(SelectEntity):
    """HDFury select entity using subscribe/sync_state pattern."""

    def __init__(
        self,
        entity_id: str,
        name: str,
        device: HDFuryDevice,
        options: list[str],
        command_fn: Callable[[str], Awaitable[bool]],
    ):
        super().__init__(
            entity_id=entity_id,
            name=name,
            features=[],
            attributes={
                Attributes.STATE: States.UNKNOWN,
                Attributes.OPTIONS: [],
                Attributes.CURRENT_OPTION: "",
            },
            cmd_handler=self._handle_command,
        )
        self._device = device
        self._options = options
        self._command_fn = command_fn
        self.subscribe_to_device(device)

    async def sync_state(self):
        self.update({
            Attributes.STATE: States.ON,
            Attributes.OPTIONS: self._options,
            Attributes.CURRENT_OPTION: self._options[0] if self._options else "",
        })

    async def _handle_command(
        self, entity: Any, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id != Commands.SELECT_OPTION:
            return StatusCodes.NOT_IMPLEMENTED

        option = params.get("option") if params else None
        if not option:
            return StatusCodes.BAD_REQUEST

        _LOG.info("[%s] Setting %s to: %s", self._device.log_id, self.name, option)
        success = await self._command_fn(option)
        return StatusCodes.OK if success else StatusCodes.SERVER_ERROR


def create_select_entities(
    config: HDFuryConfig, device: HDFuryDevice
) -> list[HDFurySelect]:
    """Create select entities for HDFury device."""
    entities: list[HDFurySelect] = []
    model = device.model_config
    device_id = config.identifier
    name = config.name

    def _add(
        key: str,
        label: str,
        options: list[str],
        command_fn: Callable[[str], Awaitable[bool]],
    ) -> None:
        if not options:
            return
        entities.append(
            HDFurySelect(
                entity_id=f"select.{device_id}.{key}",
                name=f"{name} {label}",
                device=device,
                options=options,
                command_fn=command_fn,
            )
        )

    if model.input_count > 0:
        _add(
            "input",
            "Input",
            device.source_list,
            lambda opt: device.set_source(opt),
        )

    if model.edid_modes:
        _add(
            "edid",
            "EDID Mode",
            [mode.title() for mode in model.edid_modes],
            lambda opt: device.set_edid_mode(opt.lower()),
        )

    if model.hdcp_modes:
        hdcp_options = [m.upper() if m != "1.4" else "1.4" for m in model.hdcp_modes]
        _add(
            "hdcp",
            "HDCP",
            hdcp_options,
            lambda opt: device.set_hdcp_mode("14" if opt == "1.4" else opt.lower()),
        )

    if model.edid_audio_sources:
        _add(
            "edid_audio",
            "EDID Audio",
            [src.title() for src in model.edid_audio_sources],
            lambda opt: device.set_edid_audio(opt.lower()),
        )

    if model.earc_force_modes:
        _add(
            "earc_force",
            "eARC Force",
            [mode.title() for mode in model.earc_force_modes],
            lambda opt: device.set_earc_force(opt.lower()),
        )

    if model.arc_force_modes:
        _add(
            "arc_force",
            "ARC Force",
            [mode.title() for mode in model.arc_force_modes],
            lambda opt: device.set_arc_force(opt.lower()),
        )

    if model.scale_modes:
        _add(
            "scale_mode",
            "Scale Mode",
            [mode.title() for mode in model.scale_modes],
            lambda opt: device.set_scale_mode(opt.lower()),
        )

    if model.audio_modes:
        _add(
            "audio_mode",
            "Audio Mode",
            [mode.title() for mode in model.audio_modes],
            lambda opt: device.set_audio_mode(opt.lower()),
        )

    if model.led_modes:
        led_options = list(model.led_modes.values())
        reverse_led = {v: k for k, v in model.led_modes.items()}
        _add(
            "led_mode",
            "LED Mode",
            led_options,
            lambda opt, rl=reverse_led: device.set_led_mode(rl.get(opt, "0")),
        )

    if model.color_space_modes:
        _add(
            "color_space",
            "Color Space",
            [mode.upper() for mode in model.color_space_modes],
            lambda opt: device.set_color_space(opt.lower()),
        )

    if model.deep_color_modes:
        _add(
            "deep_color",
            "Deep Color",
            [mode.title() for mode in model.deep_color_modes],
            lambda opt: device.set_deep_color(opt.lower()),
        )

    if model.output_resolutions:
        _add(
            "output_resolution",
            "Output Resolution",
            [res.upper() for res in model.output_resolutions],
            lambda opt: device.set_output_resolution(opt.lower()),
        )

    _LOG.info("Created %d select entities for %s", len(entities), name)
    return entities
