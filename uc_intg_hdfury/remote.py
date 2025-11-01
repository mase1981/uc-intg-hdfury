"""
HDFury Integration for Unfolded Circle Remote Two/3.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ucapi import Remote
from ucapi.remote import States
from ucapi.ui import UiPage, Size, create_ui_text, EntityCommand

if TYPE_CHECKING:
    from uc_intg_hdfury.device import HDFuryDevice

class HDFuryRemote(Remote):
    def __init__(self, device: HDFuryDevice):
        self._device = device
        
        ui_pages = self._build_ui_pages()
        simple_commands = self._build_simple_commands()
        
        super().__init__(
            identifier=f"{device.device_id}-remote",
            name=f"{device.name} Controls",
            features=[],
            attributes={"state": States.ON},
            simple_commands=simple_commands,
            cmd_handler=self._device.handle_remote_command,
            ui_pages=ui_pages
        )

    def _build_simple_commands(self) -> list[str]:
        """Build list of simple command IDs for activity mapping."""
        commands = []
        model_config = self._device.model_config
        
        # Source selection commands
        if model_config.input_count > 0:
            for source in self._device.source_list:
                cmd_id = f"set_source_{source.replace(' ', '_')}"
                commands.append(cmd_id)
        
        # EDID mode commands
        for mode in model_config.edid_modes:
            commands.append(f"set_edidmode_{mode}")
        
        # EDID audio source commands
        for source in model_config.edid_audio_sources:
            cmd_id = f"set_edidaudio_{source.replace('.', '')}"
            commands.append(cmd_id)
        
        # Scale mode commands
        if model_config.scale_modes:
            for mode in model_config.scale_modes:
                commands.append(f"set_scalemode_{mode}")
        
        # Audio mode commands
        if model_config.audio_modes:
            for mode in model_config.audio_modes:
                commands.append(f"set_audiomode_{mode}")

        # Led mode commands
        if model_config.led_modes:
            for mode in model_config.led_modes:
                commands.append(f"set_ledprofilevideo_{mode}")
        
        # HDR custom commands
        if model_config.hdr_custom_support:
            commands.extend([
                "set_hdrcustom_on",
                "set_hdrcustom_off"
            ])
        
        # HDR disable commands
        if model_config.hdr_disable_support:
            commands.extend([
                "set_hdrdisable_on",
                "set_hdrdisable_off"
            ])
        
        # CEC engine commands
        if model_config.cec_support:
            commands.extend([
                "set_cec_on",
                "set_cec_off"
            ])
        
        # eARC force mode commands
        for mode in model_config.earc_force_modes:
            commands.append(f"set_earcforce_{mode}")
        
        # OLED display commands
        if model_config.oled_support:
            commands.extend([
                "set_oled_on",
                "set_oled_off"
            ])
        
        # Autoswitch commands
        if model_config.autoswitch_support:
            commands.extend([
                "set_autosw_on",
                "set_autosw_off"
            ])
        
        # HDCP mode commands
        for mode in model_config.hdcp_modes:
            cmd_id = f"set_hdcp_{'14' if mode == '1.4' else mode}"
            commands.append(cmd_id)
        
        return commands

    def _build_ui_pages(self) -> list[UiPage]:
        pages = []
        model_config = self._device.model_config
        
        if model_config.input_count > 0:
            pages.append(self._create_sources_page())
        
        if model_config.edid_modes:
            pages.append(self._create_edid_page())
        
        if model_config.scale_modes:
            pages.append(self._create_scale_page())
        
        if model_config.audio_modes:
            pages.append(self._create_audio_page())
        
        if model_config.hdr_custom_support or model_config.hdr_disable_support:
            pages.append(self._create_hdr_page())
        
        if model_config.cec_support or model_config.earc_force_modes:
            pages.append(self._create_cec_earc_page())
        
        if model_config.oled_support or model_config.autoswitch_support or model_config.hdcp_modes:
            pages.append(self._create_system_page())

        if model_config.led_modes:
            pages.append(self.create_led_page())
        
        return pages

    def _create_sources_page(self) -> UiPage:
        items = [create_ui_text(text="Select Input", x=0, y=0, size=Size(width=4))]
        
        for i, source in enumerate(self._device.source_list):
            cmd_id = f"set_source_{source.replace(' ', '_')}"
            items.append(create_ui_text(
                text=source, 
                x=i, 
                y=1, 
                cmd=EntityCommand(cmd_id, {"command": cmd_id})
            ))
        
        return UiPage(page_id="sources", name="Sources", items=items)

    def _create_edid_page(self) -> UiPage:
        items = []
        y_pos = 0
        model_config = self._device.model_config

        items.append(create_ui_text(text="EDID Mode", x=0, y=y_pos, size=Size(width=5)))
        y_pos += 1
        for i, mode in enumerate(model_config.edid_modes[:5]):
            cmd_id = f"set_edidmode_{mode}"
            items.append(create_ui_text(
                text=mode.title(), 
                x=i, 
                y=y_pos, 
                cmd=EntityCommand(cmd_id, {"command": cmd_id})
            ))
        y_pos += 2

        if model_config.edid_audio_sources:
            items.append(create_ui_text(text="Audio Source", x=0, y=y_pos, size=Size(width=5)))
            y_pos += 1
            for i, source in enumerate(model_config.edid_audio_sources[:5]):
                label = "5.1" if source == "5.1" else source.title()
                cmd_id = f"set_edidaudio_{source.replace('.', '')}"
                items.append(create_ui_text(
                    text=label, 
                    x=i, 
                    y=y_pos, 
                    cmd=EntityCommand(cmd_id, {"command": cmd_id})
                ))

        return UiPage(page_id="edid", name="EDID", grid=Size(width=5, height=6), items=items)

    def _create_scale_page(self) -> UiPage:
        items = []
        y_pos = 0
        model_config = self._device.model_config

        items.append(create_ui_text(text="Scale Mode", x=0, y=y_pos, size=Size(width=5)))
        y_pos += 1
        
        for i, mode in enumerate(model_config.scale_modes[:5]):
            display_name = mode.replace("_", " ").title()
            cmd_id = f"set_scalemode_{mode}"
            items.append(create_ui_text(
                text=display_name, 
                x=i, 
                y=y_pos, 
                cmd=EntityCommand(cmd_id, {"command": cmd_id})
            ))
        
        y_pos += 2
        if len(model_config.scale_modes) > 5:
            for i, mode in enumerate(model_config.scale_modes[5:10]):
                display_name = mode.replace("_", " ").title()
                cmd_id = f"set_scalemode_{mode}"
                items.append(create_ui_text(
                    text=display_name, 
                    x=i, 
                    y=y_pos, 
                    cmd=EntityCommand(cmd_id, {"command": cmd_id})
                ))

        return UiPage(page_id="scale", name="Scale", grid=Size(width=5, height=6), items=items)

    def _create_audio_page(self) -> UiPage:
        items = []
        model_config = self._device.model_config

        items.append(create_ui_text(text="Audio Mode", x=0, y=0, size=Size(width=4)))
        for i, mode in enumerate(model_config.audio_modes):
            cmd_id = f"set_audiomode_{mode}"
            items.append(create_ui_text(
                text=mode.title(), 
                x=i, 
                y=1, 
                cmd=EntityCommand(cmd_id, {"command": cmd_id})
            ))

        return UiPage(page_id="audio", name="Audio", items=items)

    def _create_led_page(self) -> UiPage:
        items = []
        model_config = self._device.model_config

        mode_text_map = {
            "0": "Off",
            "1": "Video",
            "2": "Static",
            "3": "Blink",
            "4": "Rotate"
        }
        items.append(create_ui_text(text="Ambilight Mode", x=0, y=0, size=Size(width=4)))
        for i, mode in enumerate(model_config.led_modes):
            cmd_id = f"set_ledprofilevideo_{mode}"
            display_text = mode_text_map.get(mode, mode.title())
            items.append(create_ui_text(
                text=display_text, 
                x=i, 
                y=1, 
                cmd=EntityCommand(cmd_id, {"command": cmd_id})
            ))

        return UiPage(page_id="audio", name="Ambilight", items=items)

    def _create_hdr_page(self) -> UiPage:
        items = []
        y_pos = 0
        model_config = self._device.model_config

        if model_config.hdr_custom_support:
            items.append(create_ui_text(text="Custom HDR", x=0, y=y_pos, size=Size(width=2)))
            items.append(create_ui_text(
                text="ON", 
                x=2, 
                y=y_pos, 
                cmd=EntityCommand("set_hdrcustom_on", {"command": "set_hdrcustom_on"})
            ))
            items.append(create_ui_text(
                text="OFF", 
                x=3, 
                y=y_pos, 
                cmd=EntityCommand("set_hdrcustom_off", {"command": "set_hdrcustom_off"})
            ))
            y_pos += 1

        if model_config.hdr_disable_support:
            items.append(create_ui_text(text="Disable HDR", x=0, y=y_pos, size=Size(width=2)))
            items.append(create_ui_text(
                text="ON", 
                x=2, 
                y=y_pos, 
                cmd=EntityCommand("set_hdrdisable_on", {"command": "set_hdrdisable_on"})
            ))
            items.append(create_ui_text(
                text="OFF", 
                x=3, 
                y=y_pos, 
                cmd=EntityCommand("set_hdrdisable_off", {"command": "set_hdrdisable_off"})
            ))
        
        return UiPage(page_id="hdr", name="HDR", items=items)

    def _create_cec_earc_page(self) -> UiPage:
        items = []
        y_pos = 0
        model_config = self._device.model_config

        if model_config.cec_support:
            items.append(create_ui_text(text="CEC Engine", x=0, y=y_pos, size=Size(width=2)))
            items.append(create_ui_text(
                text="ON", 
                x=2, 
                y=y_pos, 
                cmd=EntityCommand("set_cec_on", {"command": "set_cec_on"})
            ))
            items.append(create_ui_text(
                text="OFF", 
                x=3, 
                y=y_pos, 
                cmd=EntityCommand("set_cec_off", {"command": "set_cec_off"})
            ))
            y_pos += 2
        
        if model_config.earc_force_modes:
            items.append(create_ui_text(text="eARC Force", x=0, y=y_pos, size=Size(width=4)))
            y_pos += 1
            for i, mode in enumerate(model_config.earc_force_modes[:4]):
                cmd_id = f"set_earcforce_{mode}"
                items.append(create_ui_text(
                    text=mode.title(), 
                    x=i, 
                    y=y_pos, 
                    cmd=EntityCommand(cmd_id, {"command": cmd_id})
                ))

        return UiPage(page_id="cec_earc", name="CEC/eARC", items=items)
        
    def _create_system_page(self) -> UiPage:
        items = []
        y_pos = 0
        model_config = self._device.model_config

        if model_config.oled_support:
            items.append(create_ui_text(text="OLED Display", x=0, y=y_pos, size=Size(width=2)))
            items.append(create_ui_text(
                text="ON", 
                x=2, 
                y=y_pos, 
                cmd=EntityCommand("set_oled_on", {"command": "set_oled_on"})
            ))
            items.append(create_ui_text(
                text="OFF", 
                x=3, 
                y=y_pos, 
                cmd=EntityCommand("set_oled_off", {"command": "set_oled_off"})
            ))
            y_pos += 1

        if model_config.autoswitch_support:
            items.append(create_ui_text(text="Autoswitch", x=0, y=y_pos, size=Size(width=2)))
            items.append(create_ui_text(
                text="ON", 
                x=2, 
                y=y_pos, 
                cmd=EntityCommand("set_autosw_on", {"command": "set_autosw_on"})
            ))
            items.append(create_ui_text(
                text="OFF", 
                x=3, 
                y=y_pos, 
                cmd=EntityCommand("set_autosw_off", {"command": "set_autosw_off"})
            ))
            y_pos += 2

        if model_config.hdcp_modes:
            items.append(create_ui_text(text="HDCP Mode", x=0, y=y_pos, size=Size(width=4)))
            y_pos += 1
            for i, mode in enumerate(model_config.hdcp_modes):
                cmd_id = f"set_hdcp_{'14' if mode == '1.4' else mode}"
                items.append(create_ui_text(
                    text=mode, 
                    x=i, 
                    y=y_pos, 
                    cmd=EntityCommand(cmd_id, {"command": cmd_id})
                ))

        return UiPage(page_id="system", name="System", items=items)