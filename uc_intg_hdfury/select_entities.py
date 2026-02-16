"""
HDFury Select entity implementation.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any
from ucapi import select
from ucapi.select import Select, States, Attributes, Commands

if TYPE_CHECKING:
    from uc_intg_hdfury.device import HDFuryDevice

log = logging.getLogger(__name__)


class HDFurySelectEntities:
    """Factory for creating HDFury select entities."""

    @staticmethod
    def create_select_entities(device: HDFuryDevice) -> list[Select]:
        """Create all select entities for the device."""
        entities = []
        model_config = device.model_config
        device_id = device.device_id
        device_name = device.name

        if model_config.input_count > 0:
            entities.append(HDFurySelectEntities._create_input_select(device))

        if model_config.edid_modes:
            entities.append(HDFurySelectEntities._create_edid_mode_select(device))

        if model_config.edid_audio_sources:
            entities.append(HDFurySelectEntities._create_edid_audio_select(device))

        if model_config.hdcp_modes:
            entities.append(HDFurySelectEntities._create_hdcp_mode_select(device))

        if model_config.earc_force_modes:
            entities.append(HDFurySelectEntities._create_earcforce_select(device))

        if model_config.arc_force_modes:
            entities.append(HDFurySelectEntities._create_arcforce_select(device))

        if model_config.hdr_custom_support or model_config.hdr_disable_support:
            entities.append(HDFurySelectEntities._create_hdr_mode_select(device))

        if model_config.cec_support:
            entities.append(HDFurySelectEntities._create_cec_la_select(device))

        log.info(f"Created {len(entities)} select entities for {device_name}")
        return entities

    @staticmethod
    def _create_input_select(device: HDFuryDevice) -> Select:
        """Create input source select entity."""
        options = device.source_list

        return Select(
            identifier=f"{device.device_id}-input-select",
            name=f"{device.name} Input",
            attributes={
                Attributes.STATE: States.ON,
                Attributes.OPTIONS: options,
                Attributes.CURRENT_OPTION: options[0] if options else None,
            },
            cmd_handler=lambda entity, cmd_id, params: device.handle_select_command(
                entity, cmd_id, params, "input"
            ),
        )

    @staticmethod
    def _create_edid_mode_select(device: HDFuryDevice) -> Select:
        """Create EDID mode select entity."""
        options = [mode.title() for mode in device.model_config.edid_modes]

        return Select(
            identifier=f"{device.device_id}-edid-mode-select",
            name=f"{device.name} EDID Mode",
            attributes={
                Attributes.STATE: States.ON,
                Attributes.OPTIONS: options,
                Attributes.CURRENT_OPTION: options[0] if options else None,
            },
            cmd_handler=lambda entity, cmd_id, params: device.handle_select_command(
                entity, cmd_id, params, "edid_mode"
            ),
        )

    @staticmethod
    def _create_edid_audio_select(device: HDFuryDevice) -> Select:
        """Create EDID audio source select entity."""
        raw_options = device.model_config.edid_audio_sources
        options = ["5.1" if opt == "51" else opt.title() for opt in raw_options]

        return Select(
            identifier=f"{device.device_id}-edid-audio-select",
            name=f"{device.name} EDID Audio",
            attributes={
                Attributes.STATE: States.ON,
                Attributes.OPTIONS: options,
                Attributes.CURRENT_OPTION: options[0] if options else None,
            },
            cmd_handler=lambda entity, cmd_id, params: device.handle_select_command(
                entity, cmd_id, params, "edid_audio"
            ),
        )

    @staticmethod
    def _create_hdcp_mode_select(device: HDFuryDevice) -> Select:
        """Create HDCP mode select entity."""
        raw_options = device.model_config.hdcp_modes
        options = ["1.4" if opt == "14" else opt.upper() for opt in raw_options]

        return Select(
            identifier=f"{device.device_id}-hdcp-select",
            name=f"{device.name} HDCP Mode",
            attributes={
                Attributes.STATE: States.ON,
                Attributes.OPTIONS: options,
                Attributes.CURRENT_OPTION: options[0] if options else None,
            },
            cmd_handler=lambda entity, cmd_id, params: device.handle_select_command(
                entity, cmd_id, params, "hdcp"
            ),
        )

    @staticmethod
    def _create_earcforce_select(device: HDFuryDevice) -> Select:
        """Create eARC force mode select entity."""
        earc_labels = {
            "autoearc": "Auto eARC",
            "manualearc": "Manual eARC",
            "hdmi": "Manual HDMI",
            "autoarc": "Auto ARC",
            "manualarc": "Manual ARC",
        }
        options = [earc_labels.get(mode, mode.upper()) for mode in device.model_config.earc_force_modes]

        return Select(
            identifier=f"{device.device_id}-earcforce-select",
            name=f"{device.name} eARC Mode",
            attributes={
                Attributes.STATE: States.ON,
                Attributes.OPTIONS: options,
                Attributes.CURRENT_OPTION: options[0] if options else None,
            },
            cmd_handler=lambda entity, cmd_id, params: device.handle_select_command(
                entity, cmd_id, params, "earcforce"
            ),
        )

    @staticmethod
    def _create_arcforce_select(device: HDFuryDevice) -> Select:
        """Create ARC force mode select entity."""
        options = [mode.upper() for mode in device.model_config.arc_force_modes]

        return Select(
            identifier=f"{device.device_id}-arcforce-select",
            name=f"{device.name} ARC Mode",
            attributes={
                Attributes.STATE: States.ON,
                Attributes.OPTIONS: options,
                Attributes.CURRENT_OPTION: options[0] if options else None,
            },
            cmd_handler=lambda entity, cmd_id, params: device.handle_select_command(
                entity, cmd_id, params, "arcforce"
            ),
        )

    @staticmethod
    def _create_hdr_mode_select(device: HDFuryDevice) -> Select:
        """Create HDR mode select entity."""
        options = ["Auto", "Custom", "Disabled"]

        return Select(
            identifier=f"{device.device_id}-hdr-select",
            name=f"{device.name} HDR Mode",
            attributes={
                Attributes.STATE: States.ON,
                Attributes.OPTIONS: options,
                Attributes.CURRENT_OPTION: "Auto",
            },
            cmd_handler=lambda entity, cmd_id, params: device.handle_select_command(
                entity, cmd_id, params, "hdr"
            ),
        )

    @staticmethod
    def _create_cec_la_select(device: HDFuryDevice) -> Select:
        """Create CEC logical address select entity."""
        options = ["Video", "Audio"]

        return Select(
            identifier=f"{device.device_id}-cecla-select",
            name=f"{device.name} CEC Mode",
            attributes={
                Attributes.STATE: States.ON,
                Attributes.OPTIONS: options,
                Attributes.CURRENT_OPTION: "Video",
            },
            cmd_handler=lambda entity, cmd_id, params: device.handle_select_command(
                entity, cmd_id, params, "cecla"
            ),
        )
