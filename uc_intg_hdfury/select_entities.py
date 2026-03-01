"""
HDFury Select entities.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ucapi import StatusCodes
from ucapi.select import Attributes, Commands, Select, States

if TYPE_CHECKING:
    from uc_intg_hdfury.config import HDFuryConfig
    from uc_intg_hdfury.device import HDFuryDevice

_LOG = logging.getLogger(__name__)


def create_select_entities(config: HDFuryConfig, device: HDFuryDevice) -> list[Select]:
    """Create select entities for HDFury device."""
    entities = []
    model = device.model_config
    device_id = config.identifier
    name = config.name

    if model.input_count > 0:
        options = device.source_list
        entities.append(
            Select(
                f"select.{device_id}.input",
                f"{name} Input",
                {
                    Attributes.STATE: States.ON,
                    Attributes.OPTIONS: options,
                    Attributes.CURRENT_OPTION: options[0] if options else None,
                },
                cmd_handler=_create_input_handler(device),
            )
        )

    if model.edid_modes:
        options = [mode.title() for mode in model.edid_modes]
        entities.append(
            Select(
                f"select.{device_id}.edid",
                f"{name} EDID Mode",
                {
                    Attributes.STATE: States.ON,
                    Attributes.OPTIONS: options,
                    Attributes.CURRENT_OPTION: options[0] if options else None,
                },
                cmd_handler=_create_edid_handler(device),
            )
        )

    if model.hdcp_modes:
        options = [m.upper() if m != "1.4" else "1.4" for m in model.hdcp_modes]
        entities.append(
            Select(
                f"select.{device_id}.hdcp",
                f"{name} HDCP",
                {
                    Attributes.STATE: States.ON,
                    Attributes.OPTIONS: options,
                    Attributes.CURRENT_OPTION: options[0] if options else None,
                },
                cmd_handler=_create_hdcp_handler(device),
            )
        )

    if model.edid_audio_sources:
        options = [src.title() for src in model.edid_audio_sources]
        entities.append(
            Select(
                f"select.{device_id}.edid_audio",
                f"{name} EDID Audio",
                {
                    Attributes.STATE: States.ON,
                    Attributes.OPTIONS: options,
                    Attributes.CURRENT_OPTION: options[0] if options else None,
                },
                cmd_handler=_create_edid_audio_handler(device),
            )
        )

    if model.earc_force_modes:
        options = [mode.title() for mode in model.earc_force_modes]
        entities.append(
            Select(
                f"select.{device_id}.earc_force",
                f"{name} eARC Force",
                {
                    Attributes.STATE: States.ON,
                    Attributes.OPTIONS: options,
                    Attributes.CURRENT_OPTION: options[0] if options else None,
                },
                cmd_handler=_create_earc_force_handler(device),
            )
        )

    if model.arc_force_modes:
        options = [mode.title() for mode in model.arc_force_modes]
        entities.append(
            Select(
                f"select.{device_id}.arc_force",
                f"{name} ARC Force",
                {
                    Attributes.STATE: States.ON,
                    Attributes.OPTIONS: options,
                    Attributes.CURRENT_OPTION: options[0] if options else None,
                },
                cmd_handler=_create_arc_force_handler(device),
            )
        )

    if model.scale_modes:
        options = [mode.title() for mode in model.scale_modes]
        entities.append(
            Select(
                f"select.{device_id}.scale_mode",
                f"{name} Scale Mode",
                {
                    Attributes.STATE: States.ON,
                    Attributes.OPTIONS: options,
                    Attributes.CURRENT_OPTION: options[0] if options else None,
                },
                cmd_handler=_create_scale_mode_handler(device),
            )
        )

    if model.audio_modes:
        options = [mode.title() for mode in model.audio_modes]
        entities.append(
            Select(
                f"select.{device_id}.audio_mode",
                f"{name} Audio Mode",
                {
                    Attributes.STATE: States.ON,
                    Attributes.OPTIONS: options,
                    Attributes.CURRENT_OPTION: options[0] if options else None,
                },
                cmd_handler=_create_audio_mode_handler(device),
            )
        )

    if model.led_modes:
        options = list(model.led_modes.values())
        entities.append(
            Select(
                f"select.{device_id}.led_mode",
                f"{name} LED Mode",
                {
                    Attributes.STATE: States.ON,
                    Attributes.OPTIONS: options,
                    Attributes.CURRENT_OPTION: options[0] if options else None,
                },
                cmd_handler=_create_led_mode_handler(device, model.led_modes),
            )
        )

    if model.color_space_modes:
        options = [mode.upper() for mode in model.color_space_modes]
        entities.append(
            Select(
                f"select.{device_id}.color_space",
                f"{name} Color Space",
                {
                    Attributes.STATE: States.ON,
                    Attributes.OPTIONS: options,
                    Attributes.CURRENT_OPTION: options[0] if options else None,
                },
                cmd_handler=_create_color_space_handler(device),
            )
        )

    if model.deep_color_modes:
        options = [mode.title() for mode in model.deep_color_modes]
        entities.append(
            Select(
                f"select.{device_id}.deep_color",
                f"{name} Deep Color",
                {
                    Attributes.STATE: States.ON,
                    Attributes.OPTIONS: options,
                    Attributes.CURRENT_OPTION: options[0] if options else None,
                },
                cmd_handler=_create_deep_color_handler(device),
            )
        )

    if model.output_resolutions:
        options = [res.upper() for res in model.output_resolutions]
        entities.append(
            Select(
                f"select.{device_id}.output_resolution",
                f"{name} Output Resolution",
                {
                    Attributes.STATE: States.ON,
                    Attributes.OPTIONS: options,
                    Attributes.CURRENT_OPTION: options[0] if options else None,
                },
                cmd_handler=_create_output_resolution_handler(device),
            )
        )

    _LOG.info("Created %d select entities for %s", len(entities), name)
    return entities


def _create_input_handler(device: HDFuryDevice):
    """Create input select command handler."""

    async def handler(
        entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id != Commands.SELECT_OPTION:
            return StatusCodes.NOT_IMPLEMENTED

        option = params.get("option") if params else None
        if not option:
            return StatusCodes.BAD_REQUEST

        _LOG.info("[%s] Setting input to: %s", device.log_id, option)
        success = await device.set_source(option)
        return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

    return handler


def _create_edid_handler(device: HDFuryDevice):
    """Create EDID select command handler."""

    async def handler(
        entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id != Commands.SELECT_OPTION:
            return StatusCodes.NOT_IMPLEMENTED

        option = params.get("option") if params else None
        if not option:
            return StatusCodes.BAD_REQUEST

        _LOG.info("[%s] Setting EDID mode to: %s", device.log_id, option)
        success = await device.set_edid_mode(option.lower())
        return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

    return handler


def _create_hdcp_handler(device: HDFuryDevice):
    """Create HDCP select command handler."""

    async def handler(
        entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id != Commands.SELECT_OPTION:
            return StatusCodes.NOT_IMPLEMENTED

        option = params.get("option") if params else None
        if not option:
            return StatusCodes.BAD_REQUEST

        _LOG.info("[%s] Setting HDCP mode to: %s", device.log_id, option)
        mode = "14" if option == "1.4" else option.lower()
        success = await device.set_hdcp_mode(mode)
        return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

    return handler


def _create_edid_audio_handler(device: HDFuryDevice):
    """Create EDID audio select command handler."""

    async def handler(
        entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id != Commands.SELECT_OPTION:
            return StatusCodes.NOT_IMPLEMENTED

        option = params.get("option") if params else None
        if not option:
            return StatusCodes.BAD_REQUEST

        _LOG.info("[%s] Setting EDID audio to: %s", device.log_id, option)
        success = await device.set_edid_audio(option.lower())
        return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

    return handler


def _create_earc_force_handler(device: HDFuryDevice):
    """Create eARC force select command handler."""

    async def handler(
        entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id != Commands.SELECT_OPTION:
            return StatusCodes.NOT_IMPLEMENTED

        option = params.get("option") if params else None
        if not option:
            return StatusCodes.BAD_REQUEST

        _LOG.info("[%s] Setting eARC force to: %s", device.log_id, option)
        success = await device.set_earc_force(option.lower())
        return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

    return handler


def _create_arc_force_handler(device: HDFuryDevice):
    """Create ARC force select command handler."""

    async def handler(
        entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id != Commands.SELECT_OPTION:
            return StatusCodes.NOT_IMPLEMENTED

        option = params.get("option") if params else None
        if not option:
            return StatusCodes.BAD_REQUEST

        _LOG.info("[%s] Setting ARC force to: %s", device.log_id, option)
        success = await device.set_arc_force(option.lower())
        return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

    return handler


def _create_scale_mode_handler(device: HDFuryDevice):
    """Create scale mode select command handler."""

    async def handler(
        entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id != Commands.SELECT_OPTION:
            return StatusCodes.NOT_IMPLEMENTED

        option = params.get("option") if params else None
        if not option:
            return StatusCodes.BAD_REQUEST

        _LOG.info("[%s] Setting scale mode to: %s", device.log_id, option)
        success = await device.set_scale_mode(option.lower())
        return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

    return handler


def _create_audio_mode_handler(device: HDFuryDevice):
    """Create audio mode select command handler."""

    async def handler(
        entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id != Commands.SELECT_OPTION:
            return StatusCodes.NOT_IMPLEMENTED

        option = params.get("option") if params else None
        if not option:
            return StatusCodes.BAD_REQUEST

        _LOG.info("[%s] Setting audio mode to: %s", device.log_id, option)
        success = await device.set_audio_mode(option.lower())
        return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

    return handler


def _create_led_mode_handler(device: HDFuryDevice, led_modes: dict):
    """Create LED mode select command handler."""
    reverse_map = {v: k for k, v in led_modes.items()}

    async def handler(
        entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id != Commands.SELECT_OPTION:
            return StatusCodes.NOT_IMPLEMENTED

        option = params.get("option") if params else None
        if not option:
            return StatusCodes.BAD_REQUEST

        mode_id = reverse_map.get(option, "0")
        _LOG.info("[%s] Setting LED mode to: %s (id: %s)", device.log_id, option, mode_id)
        success = await device.set_led_mode(mode_id)
        return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

    return handler


def _create_color_space_handler(device: HDFuryDevice):
    """Create color space select command handler."""

    async def handler(
        entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id != Commands.SELECT_OPTION:
            return StatusCodes.NOT_IMPLEMENTED

        option = params.get("option") if params else None
        if not option:
            return StatusCodes.BAD_REQUEST

        _LOG.info("[%s] Setting color space to: %s", device.log_id, option)
        success = await device.set_color_space(option.lower())
        return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

    return handler


def _create_deep_color_handler(device: HDFuryDevice):
    """Create deep color select command handler."""

    async def handler(
        entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id != Commands.SELECT_OPTION:
            return StatusCodes.NOT_IMPLEMENTED

        option = params.get("option") if params else None
        if not option:
            return StatusCodes.BAD_REQUEST

        _LOG.info("[%s] Setting deep color to: %s", device.log_id, option)
        success = await device.set_deep_color(option.lower())
        return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

    return handler


def _create_output_resolution_handler(device: HDFuryDevice):
    """Create output resolution select command handler."""

    async def handler(
        entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id != Commands.SELECT_OPTION:
            return StatusCodes.NOT_IMPLEMENTED

        option = params.get("option") if params else None
        if not option:
            return StatusCodes.BAD_REQUEST

        _LOG.info("[%s] Setting output resolution to: %s", device.log_id, option)
        success = await device.set_output_resolution(option.lower())
        return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

    return handler
