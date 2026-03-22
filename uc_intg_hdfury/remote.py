"""
HDFury Remote entity.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ucapi import StatusCodes
from ucapi.remote import Attributes, Commands, States
from ucapi.ui import EntityCommand, Size, UiPage, create_ui_text
from ucapi_framework import RemoteEntity

if TYPE_CHECKING:
    from uc_intg_hdfury.config import HDFuryConfig
    from uc_intg_hdfury.device import HDFuryDevice

_LOG = logging.getLogger(__name__)


class HDFuryRemote(RemoteEntity):
    """HDFury remote entity with UI pages using subscribe/sync_state pattern."""

    def __init__(self, config: HDFuryConfig, device: HDFuryDevice):
        self._device = device
        self._config = config

        ui_pages = self._build_ui_pages()
        simple_commands = self._build_simple_commands()

        super().__init__(
            entity_id=f"remote.{config.identifier}",
            name=config.name,
            features=[],
            attributes={Attributes.STATE: States.UNKNOWN},
            simple_commands=simple_commands,
            cmd_handler=self._handle_command,
            ui_pages=ui_pages,
        )
        self.subscribe_to_device(device)

    async def sync_state(self):
        self.update({Attributes.STATE: States.ON})

    async def _handle_command(
        self, entity: Any, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        if cmd_id == Commands.SEND_CMD:
            if not params or "command" not in params:
                return StatusCodes.BAD_REQUEST

            command = params["command"]
            _LOG.info("[%s] Command: %s", self._device.log_id, command)

            success = await self._execute_command(command)
            return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

        elif cmd_id == Commands.SEND_CMD_SEQUENCE:
            if not params or "sequence" not in params:
                return StatusCodes.BAD_REQUEST

            for command in params["sequence"]:
                if not await self._execute_command(command):
                    return StatusCodes.SERVER_ERROR
            return StatusCodes.OK

        return StatusCodes.NOT_IMPLEMENTED

    async def _execute_command(self, command: str) -> bool:
        if command.startswith("set_source_"):
            source = command.replace("set_source_", "").replace("_", " ")
            return await self._device.set_source(source)

        if command.startswith("set_edidmode_"):
            mode = command.replace("set_edidmode_", "")
            return await self._device.set_edid_mode(mode)

        if command.startswith("set_hdcp_"):
            mode = command.replace("set_hdcp_", "")
            return await self._device.set_hdcp_mode(mode)

        if command == "set_hdrcustom_on":
            return await self._device.set_hdr_custom(True)
        if command == "set_hdrcustom_off":
            return await self._device.set_hdr_custom(False)

        if command == "set_hdrdisable_on":
            return await self._device.set_hdr_disable(True)
        if command == "set_hdrdisable_off":
            return await self._device.set_hdr_disable(False)

        if command == "set_cec_on":
            return await self._device.set_cec(True)
        if command == "set_cec_off":
            return await self._device.set_cec(False)

        if command.startswith("set_earcforce_"):
            mode = command.replace("set_earcforce_", "")
            return await self._device.set_earc_force(mode)

        if command.startswith("set_arcforce_"):
            mode = command.replace("set_arcforce_", "")
            return await self._device.set_arc_force(mode)

        if command == "set_oled_on":
            return await self._device.set_oled(True)
        if command == "set_oled_off":
            return await self._device.set_oled(False)

        if command == "set_autosw_on":
            return await self._device.set_autoswitch(True)
        if command == "set_autosw_off":
            return await self._device.set_autoswitch(False)

        if command.startswith("set_scalemode_"):
            mode = command.replace("set_scalemode_", "")
            return await self._device.set_scale_mode(mode)

        if command.startswith("set_colorspace_"):
            mode = command.replace("set_colorspace_", "")
            return await self._device.set_color_space(mode)

        if command.startswith("set_deepcolor_"):
            mode = command.replace("set_deepcolor_", "")
            return await self._device.set_deep_color(mode)

        if command.startswith("set_edidaudio_"):
            source = command.replace("set_edidaudio_", "")
            return await self._device.set_edid_audio(source)

        if command.startswith("set_audiomode_"):
            mode = command.replace("set_audiomode_", "")
            return await self._device.set_audio_mode(mode)

        if command.startswith("set_ledmode_"):
            mode = command.replace("set_ledmode_", "")
            return await self._device.set_led_mode(mode)

        if command.startswith("set_outres_"):
            res = command.replace("set_outres_", "")
            return await self._device.set_output_resolution(res)

        if command == "hotplug":
            return await self._device.hotplug()

        if command == "reboot_device":
            return await self._device.reboot()

        return await self._device.send_command(f"set {command}")

    def _build_simple_commands(self) -> list[str]:
        commands = []
        model = self._device.model_config

        for source in self._device.source_list:
            commands.append(f"set_source_{source.replace(' ', '_')}")

        for mode in model.edid_modes:
            commands.append(f"set_edidmode_{mode}")

        for mode in model.hdcp_modes:
            commands.append(f"set_hdcp_{'14' if mode == '1.4' else mode}")

        if model.hdr_custom_support:
            commands.extend(["set_hdrcustom_on", "set_hdrcustom_off"])

        if model.hdr_disable_support:
            commands.extend(["set_hdrdisable_on", "set_hdrdisable_off"])

        if model.cec_support:
            commands.extend(["set_cec_on", "set_cec_off"])

        for mode in model.earc_force_modes:
            commands.append(f"set_earcforce_{mode}")

        if model.arc_force_modes:
            for mode in model.arc_force_modes:
                commands.append(f"set_arcforce_{mode}")

        if model.oled_support:
            commands.extend(["set_oled_on", "set_oled_off"])

        if model.autoswitch_support:
            commands.extend(["set_autosw_on", "set_autosw_off"])

        if model.scale_modes:
            for mode in model.scale_modes:
                commands.append(f"set_scalemode_{mode}")

        if model.color_space_modes:
            for mode in model.color_space_modes:
                commands.append(f"set_colorspace_{mode}")

        if model.deep_color_modes:
            for mode in model.deep_color_modes:
                commands.append(f"set_deepcolor_{mode}")

        if model.edid_audio_sources:
            for src in model.edid_audio_sources:
                commands.append(f"set_edidaudio_{src}")

        if model.audio_modes:
            for mode in model.audio_modes:
                commands.append(f"set_audiomode_{mode}")

        if model.led_modes:
            for mode_id in model.led_modes:
                commands.append(f"set_ledmode_{mode_id}")

        if model.output_resolutions:
            for res in model.output_resolutions:
                commands.append(f"set_outres_{res}")

        commands.extend(["hotplug", "reboot_device"])

        return commands

    def _build_ui_pages(self) -> list[UiPage]:
        pages = []
        model = self._device.model_config

        if model.input_count > 0:
            pages.append(self._create_sources_page())

        if model.edid_modes:
            pages.append(self._create_edid_page())

        if model.hdr_custom_support or model.hdr_disable_support:
            pages.append(self._create_hdr_page())

        if model.earc_force_modes or model.arc_force_modes:
            pages.append(self._create_audio_page())

        if model.color_space_modes or model.deep_color_modes or model.scale_modes:
            pages.append(self._create_video_page())

        pages.append(self._create_settings_page())
        pages.append(self._create_system_page())

        return pages

    def _create_sources_page(self) -> UiPage:
        items = [create_ui_text(text="Input", x=0, y=0, size=Size(width=4))]

        for i, source in enumerate(self._device.source_list):
            cmd_id = f"set_source_{source.replace(' ', '_')}"
            items.append(
                create_ui_text(
                    text=source,
                    x=i % 4,
                    y=1 + i // 4,
                    cmd=EntityCommand(cmd_id, {"command": cmd_id}),
                )
            )

        return UiPage(page_id="sources", name="Sources", items=items)

    def _create_settings_page(self) -> UiPage:
        items = []
        model = self._device.model_config
        y = 0

        if model.hdr_custom_support:
            items.append(create_ui_text(text="HDR Custom", x=0, y=y, size=Size(width=2)))
            items.append(
                create_ui_text(
                    text="ON", x=2, y=y,
                    cmd=EntityCommand("set_hdrcustom_on", {"command": "set_hdrcustom_on"}),
                )
            )
            items.append(
                create_ui_text(
                    text="OFF", x=3, y=y,
                    cmd=EntityCommand("set_hdrcustom_off", {"command": "set_hdrcustom_off"}),
                )
            )
            y += 1

        if model.cec_support:
            items.append(create_ui_text(text="CEC", x=0, y=y, size=Size(width=2)))
            items.append(
                create_ui_text(
                    text="ON", x=2, y=y,
                    cmd=EntityCommand("set_cec_on", {"command": "set_cec_on"}),
                )
            )
            items.append(
                create_ui_text(
                    text="OFF", x=3, y=y,
                    cmd=EntityCommand("set_cec_off", {"command": "set_cec_off"}),
                )
            )
            y += 1

        if model.oled_support:
            items.append(create_ui_text(text="OLED", x=0, y=y, size=Size(width=2)))
            items.append(
                create_ui_text(
                    text="ON", x=2, y=y,
                    cmd=EntityCommand("set_oled_on", {"command": "set_oled_on"}),
                )
            )
            items.append(
                create_ui_text(
                    text="OFF", x=3, y=y,
                    cmd=EntityCommand("set_oled_off", {"command": "set_oled_off"}),
                )
            )
            y += 1

        if model.autoswitch_support:
            items.append(create_ui_text(text="Auto Switch", x=0, y=y, size=Size(width=2)))
            items.append(
                create_ui_text(
                    text="ON", x=2, y=y,
                    cmd=EntityCommand("set_autosw_on", {"command": "set_autosw_on"}),
                )
            )
            items.append(
                create_ui_text(
                    text="OFF", x=3, y=y,
                    cmd=EntityCommand("set_autosw_off", {"command": "set_autosw_off"}),
                )
            )

        return UiPage(page_id="settings", name="Settings", items=items)

    def _create_edid_page(self) -> UiPage:
        items = [create_ui_text(text="EDID Mode", x=0, y=0, size=Size(width=4))]
        model = self._device.model_config

        for i, mode in enumerate(model.edid_modes[:8]):
            cmd_id = f"set_edidmode_{mode}"
            items.append(
                create_ui_text(
                    text=mode.title(),
                    x=i % 4,
                    y=1 + i // 4,
                    cmd=EntityCommand(cmd_id, {"command": cmd_id}),
                )
            )

        return UiPage(page_id="edid", name="EDID", items=items)

    def _create_hdr_page(self) -> UiPage:
        items = []
        model = self._device.model_config
        y = 0

        if model.hdr_custom_support:
            items.append(create_ui_text(text="HDR Custom", x=0, y=y, size=Size(width=2)))
            items.append(
                create_ui_text(
                    text="ON", x=2, y=y,
                    cmd=EntityCommand("set_hdrcustom_on", {"command": "set_hdrcustom_on"}),
                )
            )
            items.append(
                create_ui_text(
                    text="OFF", x=3, y=y,
                    cmd=EntityCommand("set_hdrcustom_off", {"command": "set_hdrcustom_off"}),
                )
            )
            y += 1

        if model.hdr_disable_support:
            items.append(create_ui_text(text="HDR Disable", x=0, y=y, size=Size(width=2)))
            items.append(
                create_ui_text(
                    text="ON", x=2, y=y,
                    cmd=EntityCommand("set_hdrdisable_on", {"command": "set_hdrdisable_on"}),
                )
            )
            items.append(
                create_ui_text(
                    text="OFF", x=3, y=y,
                    cmd=EntityCommand("set_hdrdisable_off", {"command": "set_hdrdisable_off"}),
                )
            )

        return UiPage(page_id="hdr", name="HDR", items=items)

    def _create_audio_page(self) -> UiPage:
        items = [create_ui_text(text="Audio Output", x=0, y=0, size=Size(width=4))]
        model = self._device.model_config
        y = 1

        if model.earc_force_modes:
            for i, mode in enumerate(model.earc_force_modes[:4]):
                cmd_id = f"set_earcforce_{mode}"
                items.append(
                    create_ui_text(
                        text=mode.title(),
                        x=i % 4,
                        y=y,
                        cmd=EntityCommand(cmd_id, {"command": cmd_id}),
                    )
                )
            y += 1

        if model.arc_force_modes:
            items.append(create_ui_text(text="ARC Mode", x=0, y=y, size=Size(width=4)))
            y += 1
            for i, mode in enumerate(model.arc_force_modes[:4]):
                cmd_id = f"set_arcforce_{mode}"
                items.append(
                    create_ui_text(
                        text=mode.title(),
                        x=i % 4,
                        y=y,
                        cmd=EntityCommand(cmd_id, {"command": cmd_id}),
                    )
                )

        return UiPage(page_id="audio", name="Audio", items=items)

    def _create_video_page(self) -> UiPage:
        items = []
        model = self._device.model_config
        y = 0

        if model.scale_modes:
            items.append(create_ui_text(text="Scale Mode", x=0, y=y, size=Size(width=4)))
            y += 1
            for i, mode in enumerate(model.scale_modes[:4]):
                cmd_id = f"set_scalemode_{mode}"
                items.append(
                    create_ui_text(
                        text=mode.title(),
                        x=i % 4,
                        y=y,
                        cmd=EntityCommand(cmd_id, {"command": cmd_id}),
                    )
                )
            y += 1

        if model.color_space_modes:
            items.append(create_ui_text(text="Color Space", x=0, y=y, size=Size(width=4)))
            y += 1
            for i, mode in enumerate(model.color_space_modes[:4]):
                cmd_id = f"set_colorspace_{mode}"
                items.append(
                    create_ui_text(
                        text=mode.upper(),
                        x=i % 4,
                        y=y,
                        cmd=EntityCommand(cmd_id, {"command": cmd_id}),
                    )
                )
            y += 1

        if model.deep_color_modes:
            items.append(create_ui_text(text="Deep Color", x=0, y=y, size=Size(width=4)))
            y += 1
            for i, mode in enumerate(model.deep_color_modes[:4]):
                cmd_id = f"set_deepcolor_{mode}"
                items.append(
                    create_ui_text(
                        text=mode.title(),
                        x=i % 4,
                        y=y,
                        cmd=EntityCommand(cmd_id, {"command": cmd_id}),
                    )
                )

        return UiPage(page_id="video", name="Video", items=items)

    def _create_system_page(self) -> UiPage:
        items = [
            create_ui_text(text="System", x=0, y=0, size=Size(width=4)),
            create_ui_text(
                text="Hotplug", x=0, y=1,
                cmd=EntityCommand("hotplug", {"command": "hotplug"}),
            ),
            create_ui_text(
                text="Reboot", x=1, y=1,
                cmd=EntityCommand("reboot_device", {"command": "reboot_device"}),
            ),
        ]

        return UiPage(page_id="system", name="System", items=items)
