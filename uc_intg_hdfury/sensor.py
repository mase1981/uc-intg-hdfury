"""
HDFury Sensor entities.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ucapi.sensor import Attributes, DeviceClasses, Options, States
from ucapi_framework import SensorEntity

if TYPE_CHECKING:
    from uc_intg_hdfury.config import HDFuryConfig
    from uc_intg_hdfury.device import HDFuryDevice

_LOG = logging.getLogger(__name__)


class HDFurySensor(SensorEntity):
    """HDFury sensor entity using subscribe/sync_state pattern."""

    def __init__(
        self,
        entity_id: str,
        name: str,
        device: HDFuryDevice,
        sensor_key: str,
        unit: str,
    ):
        super().__init__(
            entity_id=entity_id,
            name=name,
            features=[],
            attributes={
                Attributes.STATE: States.UNKNOWN,
                Attributes.VALUE: "",
            },
            device_class=DeviceClasses.CUSTOM,
            options={Options.CUSTOM_UNIT: unit},
        )
        self._device = device
        self._sensor_key = sensor_key
        self.subscribe_to_device(device)

    async def sync_state(self):
        value = self._device.get_sensor_value(self._sensor_key) or "Unknown"
        self.update({
            Attributes.STATE: States.ON,
            Attributes.VALUE: value,
        })


def create_sensors(config: HDFuryConfig, device: HDFuryDevice) -> list[HDFurySensor]:
    """Create sensor entities for HDFury device."""
    sensors: list[HDFurySensor] = []
    model = device.model_config
    device_id = config.identifier
    name = config.name

    def _add(key: str, label: str, unit: str) -> None:
        sensors.append(
            HDFurySensor(
                entity_id=f"sensor.{device_id}.{key}",
                name=f"{name} {label}",
                device=device,
                sensor_key=key,
                unit=unit,
            )
        )

    if model.input_count > 0:
        _add("current_input", "Current Input", "input")
        _add("video_input", "Video Input", "signal")

    _add("audio_rx", "Audio RX", "audio")

    if model.matrix_outputs and model.matrix_outputs >= 1:
        _add("video_tx0", "TX0 Output", "signal")
        _add("sink_tx0", "TX0 Sink", "device")
        _add("audio_tx0", "TX0 Audio", "audio")

    if model.matrix_outputs and model.matrix_outputs >= 2:
        _add("video_tx1", "TX1 Output", "signal")
        _add("sink_tx1", "TX1 Sink", "device")
        _add("audio_tx1", "TX1 Audio", "audio")

    _LOG.info("Created %d sensor entities for %s", len(sensors), name)
    return sensors
