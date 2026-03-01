"""
HDFury Sensor entities.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ucapi.sensor import Sensor, States, Attributes, DeviceClasses, Options

if TYPE_CHECKING:
    from uc_intg_hdfury.config import HDFuryConfig
    from uc_intg_hdfury.device import HDFuryDevice

_LOG = logging.getLogger(__name__)


def create_sensors(config: HDFuryConfig, device: HDFuryDevice) -> list[Sensor]:
    """Create sensor entities for HDFury device."""
    sensors = []
    model = device.model_config
    device_id = config.identifier
    name = config.name

    if model.input_count > 0:
        sensors.append(
            Sensor(
                f"sensor.{device_id}.current_input",
                f"{name} Current Input",
                [],
                {Attributes.STATE: States.ON, Attributes.VALUE: "Unknown"},
                device_class=DeviceClasses.CUSTOM,
                options={Options.CUSTOM_UNIT: "input"},
            )
        )
        sensors.append(
            Sensor(
                f"sensor.{device_id}.video_input",
                f"{name} Video Input",
                [],
                {Attributes.STATE: States.ON, Attributes.VALUE: "Unknown"},
                device_class=DeviceClasses.CUSTOM,
                options={Options.CUSTOM_UNIT: "signal"},
            )
        )

    sensors.append(
        Sensor(
            f"sensor.{device_id}.audio_rx",
            f"{name} Audio RX",
            [],
            {Attributes.STATE: States.ON, Attributes.VALUE: "Unknown"},
            device_class=DeviceClasses.CUSTOM,
            options={Options.CUSTOM_UNIT: "audio"},
        )
    )

    if model.matrix_outputs and model.matrix_outputs >= 1:
        sensors.append(
            Sensor(
                f"sensor.{device_id}.video_tx0",
                f"{name} TX0 Output",
                [],
                {Attributes.STATE: States.ON, Attributes.VALUE: "Unknown"},
                device_class=DeviceClasses.CUSTOM,
                options={Options.CUSTOM_UNIT: "signal"},
            )
        )
        sensors.append(
            Sensor(
                f"sensor.{device_id}.sink_tx0",
                f"{name} TX0 Sink",
                [],
                {Attributes.STATE: States.ON, Attributes.VALUE: "Unknown"},
                device_class=DeviceClasses.CUSTOM,
                options={Options.CUSTOM_UNIT: "device"},
            )
        )
        sensors.append(
            Sensor(
                f"sensor.{device_id}.audio_tx0",
                f"{name} TX0 Audio",
                [],
                {Attributes.STATE: States.ON, Attributes.VALUE: "Unknown"},
                device_class=DeviceClasses.CUSTOM,
                options={Options.CUSTOM_UNIT: "audio"},
            )
        )

    if model.matrix_outputs and model.matrix_outputs >= 2:
        sensors.append(
            Sensor(
                f"sensor.{device_id}.video_tx1",
                f"{name} TX1 Output",
                [],
                {Attributes.STATE: States.ON, Attributes.VALUE: "Unknown"},
                device_class=DeviceClasses.CUSTOM,
                options={Options.CUSTOM_UNIT: "signal"},
            )
        )
        sensors.append(
            Sensor(
                f"sensor.{device_id}.sink_tx1",
                f"{name} TX1 Sink",
                [],
                {Attributes.STATE: States.ON, Attributes.VALUE: "Unknown"},
                device_class=DeviceClasses.CUSTOM,
                options={Options.CUSTOM_UNIT: "device"},
            )
        )
        sensors.append(
            Sensor(
                f"sensor.{device_id}.audio_tx1",
                f"{name} TX1 Audio",
                [],
                {Attributes.STATE: States.ON, Attributes.VALUE: "Unknown"},
                device_class=DeviceClasses.CUSTOM,
                options={Options.CUSTOM_UNIT: "audio"},
            )
        )

    _LOG.info("Created %d sensor entities for %s", len(sensors), name)
    return sensors
