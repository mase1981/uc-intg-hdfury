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


def _normalise(value: str) -> str:
    return value.lower().replace(".", "").replace(" ", "").replace("_", "")


class HDFurySelect(SelectEntity):
    """HDFury select entity using subscribe/sync_state pattern."""

    def __init__(
        self,
        entity_id: str,
        name: str,
        device: HDFuryDevice,
        options: list[str],
        command_fn: Callable[[str], Awaitable[bool]],
        current_fn: Callable[[], str | None],
    ):
        super().__init__(
            entity_id,
            name,
            {
                Attributes.STATE: States.UNKNOWN,
                Attributes.OPTIONS: [],
                Attributes.CURRENT_OPTION: "",
            },
            cmd_handler=self._handle_command,
        )
        self._device = device
        self._options = options
        self._command_fn = command_fn
        self._current_fn = current_fn
        self.subscribe_to_device(device)

    def _current_option(self) -> str:
        raw = self._current_fn()
        if not raw:
            return ""
        wanted = _normalise(raw)
        for option in self._options:
            if _normalise(option) == wanted:
                return option
        return ""

    async def sync_state(self):
        if self._device.state == "UNAVAILABLE":
            self.update({Attributes.STATE: States.UNAVAILABLE})
            return
        self.update({
            Attributes.STATE: States.ON,
            Attributes.OPTIONS: list(self._options),
            Attributes.CURRENT_OPTION: self._current_option(),
        })

    async def _handle_command(
        self, entity: Any, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if not self._options:
            return StatusCodes.BAD_REQUEST
        current = self._current_option()
        index = self._options.index(current) if current in self._options else -1

        if cmd_id == Commands.SELECT_OPTION:
            option = params.get("option") if params else None
            if option not in self._options:
                return StatusCodes.BAD_REQUEST
        elif cmd_id == Commands.SELECT_FIRST:
            option = self._options[0]
        elif cmd_id == Commands.SELECT_LAST:
            option = self._options[-1]
        elif cmd_id == Commands.SELECT_NEXT:
            option = self._options[(index + 1) % len(self._options)]
        elif cmd_id == Commands.SELECT_PREVIOUS:
            option = self._options[(index - 1) % len(self._options)]
        else:
            return StatusCodes.NOT_IMPLEMENTED

        _LOG.info("[%s] Setting %s to: %s", self._device.log_id, self.name, option)
        success = await self._command_fn(option)
        if not success:
            return StatusCodes.SERVER_ERROR
        await self.sync_state()
        return StatusCodes.OK


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
        current_fn: Callable[[], str | None],
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
                current_fn=current_fn,
            )
        )

    if model.input_count > 0:
        _add(
            "input",
            "Input",
            device.source_list,
            lambda opt: device.set_source(opt),
            lambda: device.current_source,
        )

    if model.edid_modes:
        _add(
            "edid",
            "EDID Mode",
            [mode.title() for mode in model.edid_modes],
            lambda opt: device.set_edid_mode(opt.lower()),
            lambda: device.get_setting("edid"),
        )

    if model.hdcp_modes:
        hdcp_options = [m.upper() if m != "1.4" else "1.4" for m in model.hdcp_modes]
        _add(
            "hdcp",
            "HDCP",
            hdcp_options,
            lambda opt: device.set_hdcp_mode("14" if opt == "1.4" else opt.lower()),
            lambda: device.get_setting("hdcp"),
        )

    if model.edid_audio_sources:
        _add(
            "edid_audio",
            "EDID Audio",
            [src.title() for src in model.edid_audio_sources],
            lambda opt: device.set_edid_audio(opt.lower()),
            lambda: device.get_setting("edid_audio"),
        )

    if model.earc_force_modes:
        _add(
            "earc_force",
            "eARC Force",
            [mode.title() for mode in model.earc_force_modes],
            lambda opt: device.set_earc_force(opt.lower()),
            lambda: device.get_setting("earc_force"),
        )

    if model.arc_force_modes:
        _add(
            "arc_force",
            "ARC Force",
            [mode.title() for mode in model.arc_force_modes],
            lambda opt: device.set_arc_force(opt.lower()),
            lambda: device.get_setting("arc_force"),
        )

    if model.scale_modes:
        _add(
            "scale_mode",
            "Scale Mode",
            [mode.title() for mode in model.scale_modes],
            lambda opt: device.set_scale_mode(opt.lower()),
            lambda: device.get_setting("scale_mode"),
        )

    if model.audio_modes:
        _add(
            "audio_mode",
            "Audio Mode",
            [mode.title() for mode in model.audio_modes],
            lambda opt: device.set_audio_mode(opt.lower()),
            lambda: device.get_setting("audio_mode"),
        )

    if model.led_modes:
        led_options = list(model.led_modes.values())
        reverse_led = {v: k for k, v in model.led_modes.items()}
        _add(
            "led_mode",
            "LED Mode",
            led_options,
            lambda opt, rl=reverse_led: device.set_led_mode(rl.get(opt, "0")),
            lambda: model.led_modes.get(device.get_setting("led_mode") or "", ""),
        )

    if model.color_space_modes:
        _add(
            "color_space",
            "Color Space",
            [mode.upper() for mode in model.color_space_modes],
            lambda opt: device.set_color_space(opt.lower()),
            lambda: device.get_setting("color_space"),
        )

    if model.deep_color_modes:
        _add(
            "deep_color",
            "Deep Color",
            [mode.title() for mode in model.deep_color_modes],
            lambda opt: device.set_deep_color(opt.lower()),
            lambda: device.get_setting("deep_color"),
        )

    if model.output_resolutions:
        _add(
            "output_resolution",
            "Output Resolution",
            [res.upper() for res in model.output_resolutions],
            lambda opt: device.set_output_resolution(opt.lower()),
            lambda: device.get_setting("output_resolution"),
        )

    _LOG.info("Created %d select entities for %s", len(entities), name)
    return entities
