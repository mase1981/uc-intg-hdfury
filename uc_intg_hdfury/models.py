"""
HDFury Integration for Unfolded Circle Remote Two/3.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class ModelConfig:
    model_id: str
    display_name: str
    default_port: int
    input_count: int
    source_command: str
    edid_modes: List[str]
    edid_audio_sources: List[str]
    hdr_custom_support: bool
    hdr_disable_support: bool
    cec_support: bool
    earc_force_modes: List[str]
    oled_support: bool
    autoswitch_support: bool
    hdcp_modes: List[str]
    scale_modes: Optional[List[str]] = None
    audio_modes: Optional[List[str]] = None
    led_modes: Optional[Dict[str, str]] = None
    # NEW: Extended capabilities
    color_space_modes: Optional[List[str]] = None
    deep_color_modes: Optional[List[str]] = None
    output_resolutions: Optional[List[str]] = None
    matrix_outputs: Optional[int] = None  # Number of outputs for matrix switchers
    audio_delay_support: bool = False
    led_brightness_support: bool = False
    edid_slots: Optional[int] = None  # Number of custom EDID slots

VRROOM_CONFIG = ModelConfig(
    model_id="vrroom",
    display_name="VRRooM",
    default_port=2222,
    input_count=4,
    source_command="inseltx0",
    edid_modes=["automix", "custom", "fixed", "copytx0", "copytx1"],
    edid_audio_sources=["stereo", "5.1", "full", "audioout", "earcout"],
    hdr_custom_support=True,
    hdr_disable_support=True,
    cec_support=True,
    earc_force_modes=["auto", "earc", "hdmi"],
    oled_support=True,
    autoswitch_support=True,
    hdcp_modes=["auto", "1.4"],
    color_space_modes=["auto", "rgb", "ycbcr444", "ycbcr422", "ycbcr420"],
    deep_color_modes=["auto", "8bit", "10bit", "12bit"],
    output_resolutions=["auto", "4k60", "4k30", "1080p60", "1080p30"],
    edid_slots=4,
)

VERTEX2_CONFIG = ModelConfig(
    model_id="vertex2",
    display_name="VERTEX2",
    default_port=2220,
    input_count=4,
    source_command="inseltx0",
    edid_modes=["automix", "custom", "fixed", "copytx0", "copytx1"],
    edid_audio_sources=["stereo", "5.1", "full", "native", "tx1"],
    hdr_custom_support=True,
    hdr_disable_support=True,
    cec_support=True,
    earc_force_modes=["auto", "earc", "hdmi"],
    oled_support=True,
    autoswitch_support=True,
    hdcp_modes=["auto", "1.4"],
    scale_modes=["auto", "custom", "none"],
    matrix_outputs=2,  # TX0 and TX1
    color_space_modes=["auto", "rgb", "ycbcr444", "ycbcr422"],
    deep_color_modes=["auto", "8bit", "10bit", "12bit"],
    edid_slots=4,
)

VERTEX_CONFIG = ModelConfig(
    model_id="vertex",
    display_name="VERTEX",
    default_port=2220,
    input_count=2,
    source_command="input",
    edid_modes=["automix", "custom", "fixed", "copytop", "copybot"],
    edid_audio_sources=["stereo", "5.1", "7.1", "native", "top"],
    hdr_custom_support=True,
    hdr_disable_support=True,
    cec_support=True,
    earc_force_modes=[],
    oled_support=True,
    autoswitch_support=True,
    hdcp_modes=["1.4", "2.2"],
    scale_modes=["auto", "custom", "none"],
    matrix_outputs=2,  # Top and Bottom outputs
    color_space_modes=["auto", "rgb", "ycbcr444", "ycbcr422"],
    deep_color_modes=["auto", "8bit", "10bit", "12bit"],
)

DIVA_CONFIG = ModelConfig(
    model_id="diva",
    display_name="DIVA",
    default_port=2210,
    input_count=4,
    source_command="inseltx0",
    edid_modes=["automix", "custom", "fixed", "copytx0", "copytx1"],
    edid_audio_sources=["stereo", "5.1", "full", "native", "tx1"],
    hdr_custom_support=True,
    hdr_disable_support=True,
    cec_support=True,
    earc_force_modes=["auto", "earc", "hdmi"],
    oled_support=True,
    autoswitch_support=True,
    hdcp_modes=["auto", "1.4"],
    scale_modes=["auto", "custom", "none"],
    led_modes={
        "0": "Off",
        "1": "Follow",
        "2": "Static",
        "3": "Blinking",
        "4": "Pulsating",
        "5": "Rotating"
    },
    led_brightness_support=True,
    color_space_modes=["auto", "rgb", "ycbcr444", "ycbcr422"],
    deep_color_modes=["auto", "8bit", "10bit", "12bit"],
)

MAESTRO_CONFIG = ModelConfig(
    model_id="maestro",
    display_name="Maestro",
    default_port=2200,
    input_count=4,
    source_command="inseltx0",
    edid_modes=["automix", "custom", "fixed", "copytx0", "copytx1"],
    edid_audio_sources=["stereo", "5.1", "full", "native", "tx1"],
    hdr_custom_support=True,
    hdr_disable_support=True,
    cec_support=True,
    earc_force_modes=["auto", "earc", "hdmi"],
    oled_support=True,
    autoswitch_support=True,
    hdcp_modes=["auto", "1.4"],
    scale_modes=["auto", "custom", "none"],
    audio_delay_support=True,
    color_space_modes=["auto", "rgb", "ycbcr444", "ycbcr422"],
    deep_color_modes=["auto", "8bit", "10bit", "12bit"],
)

ARCANA2_CONFIG = ModelConfig(
    model_id="arcana2",
    display_name="ARCANA2",
    default_port=2222,
    input_count=1,
    source_command="",
    edid_modes=[],
    edid_audio_sources=[],
    hdr_custom_support=True,
    hdr_disable_support=False,
    cec_support=False,
    earc_force_modes=["autoearc", "manualearc", "autoarc", "manualarc", "hdmi"],
    oled_support=True,
    autoswitch_support=False,
    hdcp_modes=[],
    scale_modes=["none", "downtx1", "frltmds", "audioonly", "4k60_444_8_lldv", "4k60_444_8_hdr", "4k60_444_8_sdr"],
    audio_modes=["display", "earc", "both"],
    edid_slots=2,
)

DR8K_CONFIG = ModelConfig(
    model_id="dr8k",
    display_name="Dr.HDMI 8K",
    default_port=2201,
    input_count=1,
    source_command="",
    edid_modes=["automix", "custom", "fixed", "copytx"],
    edid_audio_sources=["stereo", "5.1", "full", "custom"],
    hdr_custom_support=False,
    hdr_disable_support=False,
    cec_support=False,
    earc_force_modes=[],
    oled_support=True,
    autoswitch_support=False,
    hdcp_modes=[],
    edid_slots=8,  # Dr.HDMI typically has many EDID slots
    output_resolutions=["auto", "4k60", "4k30", "1080p60", "1080p30", "720p60"],
)

MODEL_CONFIGS: Dict[str, ModelConfig] = {
    "vrroom": VRROOM_CONFIG,
    "vertex2": VERTEX2_CONFIG,
    "vertex": VERTEX_CONFIG,
    "diva": DIVA_CONFIG,
    "maestro": MAESTRO_CONFIG,
    "arcana2": ARCANA2_CONFIG,
    "dr8k": DR8K_CONFIG,
}

def get_model_config(model_id: str) -> ModelConfig:
    return MODEL_CONFIGS.get(model_id, VRROOM_CONFIG)

def get_source_list(model_config: ModelConfig) -> List[str]:
    if model_config.input_count == 0:
        return []
    elif model_config.input_count == 2:
        return ["Top", "Bottom"]
    else:
        return [f"HDMI {i}" for i in range(model_config.input_count)]

def format_source_for_command(source: str, model_config: ModelConfig) -> str:
    if model_config.model_id == "vertex":
        source_map = {"Top": "top", "Bottom": "bot"}
        return source_map.get(source, "top")
    else:
        return source.replace("HDMI ", "").strip()