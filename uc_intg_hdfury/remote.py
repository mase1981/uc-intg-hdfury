from __future__ import annotations
from typing import TYPE_CHECKING
from ucapi import Remote
from ucapi.ui import UiPage, Size, create_ui_text, EntityCommand

if TYPE_CHECKING:
    from uc_intg_hdfury.device import HDFuryDevice

class HDFuryRemote(Remote):
    """Defines the HDFury Remote entity and its custom UI."""
    def __init__(self, device: HDFuryDevice):
        self._device = device
        
        super().__init__(
            identifier=f"{device.media_player_entity.id}-remote",
            name=f"{device.name} Controls",
            features=[],
            attributes={},
            cmd_handler=self._device.handle_remote_command,
            ui_pages=[
                self._create_sources_page(device.source_list),
                self._create_edid_page(),
                self._create_hdr_avi_page(),
                self._create_cec_earc_page(),
                self._create_system_page(),
            ]
        )

    def _create_sources_page(self, source_list: list[str]) -> UiPage:
        items = [create_ui_text(text="Select Input", x=0, y=0, size=Size(width=4))]
        
        for i, source in enumerate(source_list):
            cmd_id = f"set_source_{source.replace(' ', '_')}"
            items.append(create_ui_text(text=source, x=i, y=1, cmd=EntityCommand(cmd_id)))
        
        return UiPage(page_id="sources", name="Sources", items=items)

    def _create_edid_page(self) -> UiPage:
        items = []
        y_pos = 0

        items.append(create_ui_text(text="EDID Mode", x=0, y=y_pos, size=Size(width=5)))
        y_pos += 1
        edid_modes = ["automix", "custom", "fixed", "copytx0", "copytx1"]
        for i, mode in enumerate(edid_modes):
            cmd_id = f"set_edidmode_{mode}"
            items.append(create_ui_text(text=mode.title(), x=i, y=y_pos, cmd=EntityCommand(cmd_id)))
        y_pos += 2

        items.append(create_ui_text(text="Automix Audio Source", x=0, y=y_pos, size=Size(width=5)))
        y_pos += 1
        audio_sources = ["stereo", "51", "full", "audioout", "earcout"]
        for i, source in enumerate(audio_sources):
            label = "5.1" if source == "51" else source.title()
            cmd_id = f"set_edidaudio_{source}"
            items.append(create_ui_text(text=label, x=i, y=y_pos, cmd=EntityCommand(cmd_id)))

        return UiPage(page_id="edid", name="EDID", grid=Size(width=5, height=6), items=items)

    def _create_hdr_avi_page(self) -> UiPage:
        items = []
        items.append(create_ui_text(text="Custom HDR", x=0, y=0, size=Size(width=2)))
        items.append(create_ui_text(text="ON", x=2, y=0, cmd=EntityCommand("set_hdrcustom_on")))
        items.append(create_ui_text(text="OFF", x=3, y=0, cmd=EntityCommand("set_hdrcustom_off")))

        items.append(create_ui_text(text="Disable HDR", x=0, y=1, size=Size(width=2)))
        items.append(create_ui_text(text="ON", x=2, y=1, cmd=EntityCommand("set_hdrdisable_on")))
        items.append(create_ui_text(text="OFF", x=3, y=1, cmd=EntityCommand("set_hdrdisable_off")))
        
        return UiPage(page_id="hdr_avi", name="HDR/AVI", items=items)

    def _create_cec_earc_page(self) -> UiPage:
        items = []
        items.append(create_ui_text(text="CEC Engine", x=0, y=0, size=Size(width=2)))
        items.append(create_ui_text(text="ON", x=2, y=0, cmd=EntityCommand("set_cec_on")))
        items.append(create_ui_text(text="OFF", x=3, y=0, cmd=EntityCommand("set_cec_off")))
        
        y_pos = 2
        items.append(create_ui_text(text="eARC Force Mode", x=0, y=y_pos, size=Size(width=4)))
        y_pos += 1
        earc_modes = ["auto", "earc", "hdmi"]
        for i, mode in enumerate(earc_modes):
            cmd_id = f"set_earcforce_{mode}"
            items.append(create_ui_text(text=mode.title(), x=i, y=y_pos, cmd=EntityCommand(cmd_id)))

        return UiPage(page_id="cec_earc", name="CEC/eARC", items=items)
        
    def _create_system_page(self) -> UiPage:
        items = []
        items.append(create_ui_text(text="OLED Display", x=0, y=0, size=Size(width=2)))
        items.append(create_ui_text(text="ON", x=2, y=0, cmd=EntityCommand("set_oled_on")))
        items.append(create_ui_text(text="OFF", x=3, y=0, cmd=EntityCommand("set_oled_off")))

        items.append(create_ui_text(text="Autoswitch", x=0, y=1, size=Size(width=2)))
        items.append(create_ui_text(text="ON", x=2, y=1, cmd=EntityCommand("set_autosw_on")))
        items.append(create_ui_text(text="OFF", x=3, y=1, cmd=EntityCommand("set_autosw_off")))

        y_pos = 3
        items.append(create_ui_text(text="HDCP Mode", x=0, y=y_pos, size=Size(width=4)))
        y_pos += 1
        hdcp_modes = ["auto", "1.4"]
        for i, mode in enumerate(hdcp_modes):
            cmd_id = f"set_hdcp_{'14' if mode == '1.4' else mode}"
            items.append(create_ui_text(text=mode, x=i, y=y_pos, cmd=EntityCommand(cmd_id)))

        return UiPage(page_id="system", name="System", items=items)
