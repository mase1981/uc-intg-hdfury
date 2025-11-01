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
        
        # Matrix output routing (VERTEX/VERTEX2)
        if model_config.matrix_outputs:
            for output_num in range(model_config.matrix_outputs):
                for source in self._device.source_list:
                    cmd_id = f"route_tx{output_num}_{source.replace(' ', '_')}"
                    commands.append(cmd_id)
        
        # EDID mode commands
        for mode in model_config.edid_modes:
            commands.append(f"set_edidmode_{mode}")
        
        # EDID audio source commands
        for source in model_config.edid_audio_sources:
            cmd_id = f"set_edidaudio_{source.replace('.', '')}"
            commands.append(cmd_id)
        
        # EDID slot commands
        if model_config.edid_slots:
            for slot in range(1, model_config.edid_slots + 1):
                commands.append(f"load_edid_slot_{slot}")
                commands.append(f"save_edid_slot_{slot}")
        
        # Color space commands
        if model_config.color_space_modes:
            for mode in model_config.color_space_modes:
                commands.append(f"set_colorspace_{mode}")
        
        # Deep color commands
        if model_config.deep_color_modes:
            for mode in model_config.deep_color_modes:
                commands.append(f"set_deepcolor_{mode}")
        
        # Output resolution commands
        if model_config.output_resolutions:
            for res in model_config.output_resolutions:
                commands.append(f"set_resolution_{res}")
        
        # Scale mode commands
        if model_config.scale_modes:
            for mode in model_config.scale_modes:
                commands.append(f"set_scalemode_{mode}")
        
        # Audio mode commands
        if model_config.audio_modes:
            for mode in model_config.audio_modes:
                commands.append(f"set_audiomode_{mode}")
        
        # Audio delay commands (Maestro)
        if model_config.audio_delay_support:
            commands.extend([
                "audio_delay_plus",
                "audio_delay_minus",
                "audio_delay_reset"
            ])
        
        # LED/Ambilight mode commands (DIVA only)
        if model_config.led_modes:
            for mode_id in model_config.led_modes.keys():
                commands.append(f"set_ledmode_{mode_id}")
        
        # LED brightness commands (DIVA only)
        if model_config.led_brightness_support:
            commands.extend([
                "led_brightness_up",
                "led_brightness_down",
                "set_led_brightness_25",
                "set_led_brightness_50",
                "set_led_brightness_75",
                "set_led_brightness_100"
            ])
        
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
        
        # Device info commands (all models)
        commands.extend([
            "get_firmware_version",
            "get_device_info"
        ])
        
        return commands

    def _build_ui_pages(self) -> list[UiPage]:
        pages = []
        model_config = self._device.model_config
        
        if model_config.input_count > 0:
            pages.append(self._create_sources_page())
        
        # Matrix routing page for VERTEX/VERTEX2
        if model_config.matrix_outputs:
            pages.append(self._create_matrix_page())
        
        if model_config.edid_modes:
            pages.append(self._create_edid_page())
        
        # Video settings page (color space, deep color, resolution)
        if (model_config.color_space_modes or 
            model_config.deep_color_modes or 
            model_config.output_resolutions):
            pages.append(self._create_video_page())
        
        if model_config.scale_modes:
            pages.append(self._create_scale_page())
        
        if model_config.audio_modes or model_config.audio_delay_support:
            pages.append(self._create_audio_page())
        
        # LED/Ambilight page for DIVA
        if model_config.led_modes:
            pages.append(self._create_led_page())
        
        if model_config.hdr_custom_support or model_config.hdr_disable_support:
            pages.append(self._create_hdr_page())
        
        if model_config.cec_support or model_config.earc_force_modes:
            pages.append(self._create_cec_earc_page())
        
        if model_config.oled_support or model_config.autoswitch_support or model_config.hdcp_modes:
            pages.append(self._create_system_page())
        
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

    def _create_matrix_page(self) -> UiPage:
        """Create matrix routing page for VERTEX/VERTEX2."""
        items = []
        model_config = self._device.model_config
        
        items.append(create_ui_text(text="Matrix Routing", x=0, y=0, size=Size(width=4)))
        
        row = 1
        for output_num in range(model_config.matrix_outputs):
            output_name = f"TX{output_num}" if model_config.model_id != "vertex" else ("Top" if output_num == 0 else "Bottom")
            items.append(create_ui_text(text=output_name, x=0, y=row, size=Size(width=1)))
            
            col = 1
            for source in self._device.source_list[:3]:  # Limit to 3 sources per row
                cmd_id = f"route_tx{output_num}_{source.replace(' ', '_')}"
                items.append(create_ui_text(
                    text=source[:6], 
                    x=col, 
                    y=row, 
                    cmd=EntityCommand(cmd_id, {"command": cmd_id})
                ))
                col += 1
            
            row += 1

        return UiPage(page_id="matrix", name="Matrix", items=items)

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

    def _create_video_page(self) -> UiPage:
        """Create video settings page (color space, deep color, resolution)."""
        items = []
        y_pos = 0
        model_config = self._device.model_config

        # Color space section
        if model_config.color_space_modes:
            items.append(create_ui_text(text="Color Space", x=0, y=y_pos, size=Size(width=5)))
            y_pos += 1
            for i, mode in enumerate(model_config.color_space_modes[:5]):
                cmd_id = f"set_colorspace_{mode}"
                label = mode.upper() if len(mode) <= 6 else mode[:6]
                items.append(create_ui_text(
                    text=label, 
                    x=i, 
                    y=y_pos, 
                    cmd=EntityCommand(cmd_id, {"command": cmd_id})
                ))
            y_pos += 2

        # Deep color section
        if model_config.deep_color_modes:
            items.append(create_ui_text(text="Bit Depth", x=0, y=y_pos, size=Size(width=4)))
            y_pos += 1
            for i, mode in enumerate(model_config.deep_color_modes[:4]):
                cmd_id = f"set_deepcolor_{mode}"
                items.append(create_ui_text(
                    text=mode.upper(), 
                    x=i, 
                    y=y_pos, 
                    cmd=EntityCommand(cmd_id, {"command": cmd_id})
                ))
            y_pos += 2

        # Output resolution section
        if model_config.output_resolutions:
            items.append(create_ui_text(text="Resolution", x=0, y=y_pos, size=Size(width=4)))
            y_pos += 1
            col = 0
            for res in model_config.output_resolutions[:8]:
                if y_pos >= 6:
                    break
                cmd_id = f"set_resolution_{res}"
                items.append(create_ui_text(
                    text=res.upper(), 
                    x=col, 
                    y=y_pos, 
                    cmd=EntityCommand(cmd_id, {"command": cmd_id})
                ))
                col += 1
                if col >= 4:
                    col = 0
                    y_pos += 1

        return UiPage(page_id="video", name="Video", grid=Size(width=5, height=6), items=items)

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
        y_pos = 0
        model_config = self._device.model_config

        # Audio modes (ARCANA2)
        if model_config.audio_modes:
            items.append(create_ui_text(text="Audio Mode", x=0, y=y_pos, size=Size(width=4)))
            y_pos += 1
            for i, mode in enumerate(model_config.audio_modes):
                cmd_id = f"set_audiomode_{mode}"
                items.append(create_ui_text(
                    text=mode.title(), 
                    x=i, 
                    y=y_pos, 
                    cmd=EntityCommand(cmd_id, {"command": cmd_id})
                ))
            y_pos += 2

        # Audio delay (Maestro)
        if model_config.audio_delay_support:
            items.append(create_ui_text(text="Lip Sync", x=0, y=y_pos, size=Size(width=3)))
            items.append(create_ui_text(
                text="-", 
                x=0, 
                y=y_pos + 1, 
                cmd=EntityCommand("audio_delay_minus", {"command": "audio_delay_minus"})
            ))
            items.append(create_ui_text(
                text="Reset", 
                x=1, 
                y=y_pos + 1, 
                cmd=EntityCommand("audio_delay_reset", {"command": "audio_delay_reset"})
            ))
            items.append(create_ui_text(
                text="+", 
                x=2, 
                y=y_pos + 1, 
                cmd=EntityCommand("audio_delay_plus", {"command": "audio_delay_plus"})
            ))

        return UiPage(page_id="audio", name="Audio", items=items)

    def _create_led_page(self) -> UiPage:
        """Create LED/Ambilight control page (DIVA only)."""
        items = []
        model_config = self._device.model_config

        items.append(create_ui_text(text="LED Mode", x=0, y=0, size=Size(width=4)))
        
        row, col = 1, 0
        for mode_id, mode_name in model_config.led_modes.items():
            cmd_id = f"set_ledmode_{mode_id}"
            items.append(create_ui_text(
                text=mode_name, 
                x=col, 
                y=row, 
                cmd=EntityCommand(cmd_id, {"command": cmd_id})
            ))
            
            col += 1
            if col >= 4:
                col = 0
                row += 1

        # LED brightness controls
        if model_config.led_brightness_support:
            row += 1
            items.append(create_ui_text(text="Brightness", x=0, y=row, size=Size(width=2)))
            items.append(create_ui_text(
                text="-", 
                x=2, 
                y=row, 
                cmd=EntityCommand("led_brightness_down", {"command": "led_brightness_down"})
            ))
            items.append(create_ui_text(
                text="+", 
                x=3, 
                y=row, 
                cmd=EntityCommand("led_brightness_up", {"command": "led_brightness_up"})
            ))
            
            row += 1
            presets = [("25%", "25"), ("50%", "50"), ("75%", "75"), ("100%", "100")]
            for i, (label, value) in enumerate(presets):
                cmd_id = f"set_led_brightness_{value}"
                items.append(create_ui_text(
                    text=label, 
                    x=i, 
                    y=row, 
                    cmd=EntityCommand(cmd_id, {"command": cmd_id})
                ))

        return UiPage(page_id="led", name="LED/Ambilight", items=items)

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