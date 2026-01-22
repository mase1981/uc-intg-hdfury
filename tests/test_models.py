"""
Tests for HDFury Models

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""
import pytest
from uc_intg_hdfury.models import (
    MODEL_CONFIGS,
    VRROOM_CONFIG,
    VERTEX2_CONFIG,
    VERTEX_CONFIG,
    DIVA_CONFIG,
    MAESTRO_CONFIG,
    ARCANA2_CONFIG,
    DR8K_CONFIG,
    get_model_config,
    get_source_list,
    format_source_for_command
)


def test_all_models_registered():
    """Test all model configs are registered in MODEL_CONFIGS dict."""
    expected_models = ["vrroom", "vertex2", "vertex", "diva", "maestro", "arcana2", "dr8k"]

    for model_id in expected_models:
        assert model_id in MODEL_CONFIGS, f"Model {model_id} not found in MODEL_CONFIGS"


def test_vrroom_config():
    """Test VRRooM configuration."""
    assert VRROOM_CONFIG.model_id == "vrroom"
    assert VRROOM_CONFIG.display_name == "VRRooM"
    assert VRROOM_CONFIG.default_port == 2222
    assert VRROOM_CONFIG.input_count == 4
    assert VRROOM_CONFIG.source_command == "inseltx0"
    assert VRROOM_CONFIG.oled_support is True
    assert VRROOM_CONFIG.cec_support is True
    assert VRROOM_CONFIG.autoswitch_support is True


def test_vertex2_config():
    """Test VERTEX2 configuration."""
    assert VERTEX2_CONFIG.model_id == "vertex2"
    assert VERTEX2_CONFIG.default_port == 2220
    assert VERTEX2_CONFIG.matrix_outputs == 2
    assert VERTEX2_CONFIG.scale_modes is not None


def test_vertex_config():
    """Test VERTEX configuration."""
    assert VERTEX_CONFIG.model_id == "vertex"
    assert VERTEX_CONFIG.input_count == 2
    assert VERTEX_CONFIG.source_command == "input"
    assert VERTEX_CONFIG.matrix_outputs == 2


def test_diva_config():
    """Test DIVA configuration."""
    assert DIVA_CONFIG.model_id == "diva"
    assert DIVA_CONFIG.led_modes is not None
    assert DIVA_CONFIG.led_brightness_support is True
    assert len(DIVA_CONFIG.led_modes) > 0


def test_maestro_config():
    """Test Maestro configuration."""
    assert MAESTRO_CONFIG.model_id == "maestro"
    assert MAESTRO_CONFIG.default_port == 2200
    assert MAESTRO_CONFIG.arc_force_modes is not None


def test_arcana2_config():
    """Test ARCANA2 configuration."""
    assert ARCANA2_CONFIG.model_id == "arcana2"
    assert ARCANA2_CONFIG.input_count == 1
    assert ARCANA2_CONFIG.audio_modes is not None
    assert ARCANA2_CONFIG.scale_modes is not None


def test_dr8k_config():
    """Test Dr.HDMI 8K configuration."""
    assert DR8K_CONFIG.model_id == "dr8k"
    assert DR8K_CONFIG.edid_slots == 8
    assert DR8K_CONFIG.output_resolutions is not None


def test_get_model_config_valid():
    """Test get_model_config returns correct config for valid model ID."""
    for model_id in ["vrroom", "vertex2", "vertex", "diva", "maestro", "arcana2", "dr8k"]:
        config = get_model_config(model_id)
        assert config.model_id == model_id


def test_get_model_config_invalid_defaults_to_vrroom():
    """Test get_model_config defaults to VRRooM for invalid model ID."""
    config = get_model_config("invalid_model")
    assert config.model_id == "vrroom"


def test_get_source_list_4_inputs():
    """Test get_source_list for 4-input devices."""
    sources = get_source_list(VRROOM_CONFIG)
    assert sources == ["HDMI 0", "HDMI 1", "HDMI 2", "HDMI 3"]


def test_get_source_list_2_inputs_vertex():
    """Test get_source_list for VERTEX (2 inputs)."""
    sources = get_source_list(VERTEX_CONFIG)
    assert sources == ["Top", "Bottom"]


def test_get_source_list_no_inputs():
    """Test get_source_list for devices with no inputs."""
    sources = get_source_list(ARCANA2_CONFIG)
    assert sources == []


def test_format_source_for_command_standard():
    """Test format_source_for_command for standard devices."""
    result = format_source_for_command("HDMI 1", VRROOM_CONFIG)
    assert result == "1"

    result = format_source_for_command("HDMI 3", DIVA_CONFIG)
    assert result == "3"


def test_format_source_for_command_vertex():
    """Test format_source_for_command for VERTEX."""
    result = format_source_for_command("Top", VERTEX_CONFIG)
    assert result == "top"

    result = format_source_for_command("Bottom", VERTEX_CONFIG)
    assert result == "bot"


def test_all_configs_have_required_fields():
    """Test all model configs have required fields."""
    required_fields = [
        "model_id",
        "display_name",
        "default_port",
        "input_count",
        "edid_modes",
        "edid_audio_sources",
        "hdr_custom_support",
        "hdr_disable_support",
        "cec_support",
        "earc_force_modes",
        "oled_support",
        "autoswitch_support",
        "hdcp_modes"
    ]

    for model_id, config in MODEL_CONFIGS.items():
        for field in required_fields:
            assert hasattr(config, field), f"{model_id} missing required field: {field}"


def test_edid_modes_not_empty_where_applicable():
    """Test EDID modes are defined for devices that need them."""
    devices_with_edid = ["vrroom", "vertex2", "vertex", "diva", "maestro", "dr8k"]

    for model_id in devices_with_edid:
        config = get_model_config(model_id)
        assert len(config.edid_modes) > 0, f"{model_id} should have EDID modes"


def test_earc_force_modes_present():
    """Test eARC force modes are present where supported."""
    configs_with_earc = [VRROOM_CONFIG, VERTEX2_CONFIG, DIVA_CONFIG, MAESTRO_CONFIG, ARCANA2_CONFIG]

    for config in configs_with_earc:
        assert len(config.earc_force_modes) > 0, f"{config.model_id} should have eARC force modes"
