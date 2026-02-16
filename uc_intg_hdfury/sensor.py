"""
HDFury Sensor entity implementation.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""
import logging
from typing import Any
from ucapi import sensor
from ucapi.sensor import Sensor, States, Attributes, DeviceClasses, Options

log = logging.getLogger(__name__)


class HDFurySensor:
    """HDFury sensor entity factory."""

    @staticmethod
    def create_sensors(device_id: str, device_name: str, model_config: Any) -> list[Sensor]:
        """
        Create sensor entities for HDFury device.

        Args:
            device_id: Unique device identifier
            device_name: Friendly device name
            model_config: Model configuration object

        Returns:
            List of sensor entities
        """
        sensors = []

        sensors.append(Sensor(
            identifier=f"{device_id}-connection",
            name=f"{device_name} Connection",
            features=[],
            attributes={
                Attributes.STATE: States.UNKNOWN,
                Attributes.VALUE: "Unknown",
            },
            device_class=DeviceClasses.CUSTOM,
            options={
                Options.CUSTOM_UNIT: "status"
            }
        ))

        sensors.append(Sensor(
            identifier=f"{device_id}-firmware",
            name=f"{device_name} Firmware",
            features=[],
            attributes={
                Attributes.STATE: States.UNKNOWN,
                Attributes.VALUE: "Unknown",
            },
            device_class=DeviceClasses.CUSTOM,
            options={
                Options.CUSTOM_UNIT: "version"
            }
        ))

        if model_config.input_count > 0:
            sensors.append(Sensor(
                identifier=f"{device_id}-current-input",
                name=f"{device_name} Current Input",
                features=[],
                attributes={
                    Attributes.STATE: States.UNKNOWN,
                    Attributes.VALUE: "Unknown",
                },
                device_class=DeviceClasses.CUSTOM,
                options={
                    Options.CUSTOM_UNIT: "input"
                }
            ))

        if len(model_config.edid_modes) > 0:
            sensors.append(Sensor(
                identifier=f"{device_id}-edid-mode",
                name=f"{device_name} EDID Mode",
                features=[],
                attributes={
                    Attributes.STATE: States.UNKNOWN,
                    Attributes.VALUE: "Unknown",
                },
                device_class=DeviceClasses.CUSTOM,
                options={
                    Options.CUSTOM_UNIT: "mode"
                }
            ))

        if model_config.hdr_custom_support or model_config.hdr_disable_support:
            sensors.append(Sensor(
                identifier=f"{device_id}-hdr-mode",
                name=f"{device_name} HDR Mode",
                features=[],
                attributes={
                    Attributes.STATE: States.UNKNOWN,
                    Attributes.VALUE: "Unknown",
                },
                device_class=DeviceClasses.CUSTOM,
                options={
                    Options.CUSTOM_UNIT: "mode"
                }
            ))

        if model_config.hdcp_modes and len(model_config.hdcp_modes) > 0:
            sensors.append(Sensor(
                identifier=f"{device_id}-hdcp-mode",
                name=f"{device_name} HDCP Mode",
                features=[],
                attributes={
                    Attributes.STATE: States.UNKNOWN,
                    Attributes.VALUE: "Unknown",
                },
                device_class=DeviceClasses.CUSTOM,
                options={
                    Options.CUSTOM_UNIT: "mode"
                }
            ))

        if model_config.oled_support:
            sensors.append(Sensor(
                identifier=f"{device_id}-oled-status",
                name=f"{device_name} OLED Display",
                features=[],
                attributes={
                    Attributes.STATE: States.UNKNOWN,
                    Attributes.VALUE: "Unknown",
                },
                device_class=DeviceClasses.BINARY,
                options={
                    Options.CUSTOM_UNIT: "power"
                }
            ))

        if model_config.autoswitch_support:
            sensors.append(Sensor(
                identifier=f"{device_id}-autoswitch-status",
                name=f"{device_name} Autoswitch",
                features=[],
                attributes={
                    Attributes.STATE: States.UNKNOWN,
                    Attributes.VALUE: "Unknown",
                },
                device_class=DeviceClasses.BINARY,
                options={
                    Options.CUSTOM_UNIT: "switch"
                }
            ))

        if model_config.color_space_modes:
            sensors.append(Sensor(
                identifier=f"{device_id}-colorspace",
                name=f"{device_name} Color Space",
                features=[],
                attributes={
                    Attributes.STATE: States.UNKNOWN,
                    Attributes.VALUE: "Unknown",
                },
                device_class=DeviceClasses.CUSTOM,
                options={
                    Options.CUSTOM_UNIT: "mode"
                }
            ))

        if model_config.deep_color_modes:
            sensors.append(Sensor(
                identifier=f"{device_id}-deep-color",
                name=f"{device_name} Deep Color",
                features=[],
                attributes={
                    Attributes.STATE: States.UNKNOWN,
                    Attributes.VALUE: "Unknown",
                },
                device_class=DeviceClasses.CUSTOM,
                options={
                    Options.CUSTOM_UNIT: "bit depth"
                }
            ))

        if model_config.matrix_outputs and model_config.matrix_outputs >= 1:
            sensors.append(Sensor(
                identifier=f"{device_id}-audio-tx0",
                name=f"{device_name} Audio TX0",
                features=[],
                attributes={
                    Attributes.STATE: States.UNKNOWN,
                    Attributes.VALUE: "Unknown",
                },
                device_class=DeviceClasses.CUSTOM,
                options={
                    Options.CUSTOM_UNIT: "audio"
                }
            ))

        if model_config.matrix_outputs and model_config.matrix_outputs >= 2:
            sensors.append(Sensor(
                identifier=f"{device_id}-audio-tx1",
                name=f"{device_name} Audio TX1",
                features=[],
                attributes={
                    Attributes.STATE: States.UNKNOWN,
                    Attributes.VALUE: "Unknown",
                },
                device_class=DeviceClasses.CUSTOM,
                options={
                    Options.CUSTOM_UNIT: "audio"
                }
            ))

        if model_config.model_id in ["vrroom", "vertex2", "vertex", "diva", "maestro"]:
            sensors.append(Sensor(
                identifier=f"{device_id}-audio-out",
                name=f"{device_name} Audio Out",
                features=[],
                attributes={
                    Attributes.STATE: States.UNKNOWN,
                    Attributes.VALUE: "Unknown",
                },
                device_class=DeviceClasses.CUSTOM,
                options={
                    Options.CUSTOM_UNIT: "audio"
                }
            ))

        if model_config.input_count > 0:
            sensors.append(Sensor(
                identifier=f"{device_id}-video-input",
                name=f"{device_name} Video Input",
                features=[],
                attributes={
                    Attributes.STATE: States.UNKNOWN,
                    Attributes.VALUE: "Unknown",
                },
                device_class=DeviceClasses.CUSTOM,
                options={
                    Options.CUSTOM_UNIT: "video"
                }
            ))

        if model_config.matrix_outputs and model_config.matrix_outputs >= 1:
            sensors.append(Sensor(
                identifier=f"{device_id}-video-tx0",
                name=f"{device_name} Video TX0",
                features=[],
                attributes={
                    Attributes.STATE: States.UNKNOWN,
                    Attributes.VALUE: "Unknown",
                },
                device_class=DeviceClasses.CUSTOM,
                options={
                    Options.CUSTOM_UNIT: "video"
                }
            ))
            sensors.append(Sensor(
                identifier=f"{device_id}-sink-tx0",
                name=f"{device_name} Sink TX0",
                features=[],
                attributes={
                    Attributes.STATE: States.UNKNOWN,
                    Attributes.VALUE: "Unknown",
                },
                device_class=DeviceClasses.CUSTOM,
                options={
                    Options.CUSTOM_UNIT: "sink"
                }
            ))

        if model_config.matrix_outputs and model_config.matrix_outputs >= 2:
            sensors.append(Sensor(
                identifier=f"{device_id}-video-tx1",
                name=f"{device_name} Video TX1",
                features=[],
                attributes={
                    Attributes.STATE: States.UNKNOWN,
                    Attributes.VALUE: "Unknown",
                },
                device_class=DeviceClasses.CUSTOM,
                options={
                    Options.CUSTOM_UNIT: "video"
                }
            ))
            sensors.append(Sensor(
                identifier=f"{device_id}-sink-tx1",
                name=f"{device_name} Sink TX1",
                features=[],
                attributes={
                    Attributes.STATE: States.UNKNOWN,
                    Attributes.VALUE: "Unknown",
                },
                device_class=DeviceClasses.CUSTOM,
                options={
                    Options.CUSTOM_UNIT: "sink"
                }
            ))

        log.info(f"Created {len(sensors)} sensor entities for {device_name}")
        return sensors

    @staticmethod
    def update_connection_sensor(sensor: Sensor, connected: bool) -> None:
        """Update connection sensor state."""
        sensor.attributes[Attributes.STATE] = States.ON if connected else States.UNAVAILABLE
        sensor.attributes[Attributes.VALUE] = "Connected" if connected else "Disconnected"

    @staticmethod
    def update_firmware_sensor(sensor: Sensor, version: str) -> None:
        """Update firmware version sensor."""
        sensor.attributes[Attributes.STATE] = States.ON
        sensor.attributes[Attributes.VALUE] = version

    @staticmethod
    def update_input_sensor(sensor: Sensor, input_name: str) -> None:
        """Update current input sensor."""
        sensor.attributes[Attributes.STATE] = States.ON
        sensor.attributes[Attributes.VALUE] = input_name

    @staticmethod
    def update_edid_mode_sensor(sensor: Sensor, mode: str) -> None:
        """Update EDID mode sensor."""
        sensor.attributes[Attributes.STATE] = States.ON
        sensor.attributes[Attributes.VALUE] = mode

    @staticmethod
    def update_hdr_mode_sensor(sensor: Sensor, mode: str) -> None:
        """Update HDR mode sensor."""
        sensor.attributes[Attributes.STATE] = States.ON
        sensor.attributes[Attributes.VALUE] = mode

    @staticmethod
    def update_hdcp_mode_sensor(sensor: Sensor, mode: str) -> None:
        """Update HDCP mode sensor."""
        sensor.attributes[Attributes.STATE] = States.ON
        sensor.attributes[Attributes.VALUE] = mode

    @staticmethod
    def update_oled_status_sensor(sensor: Sensor, enabled: bool) -> None:
        """Update OLED status sensor."""
        sensor.attributes[Attributes.STATE] = States.ON
        sensor.attributes[Attributes.VALUE] = "ON" if enabled else "OFF"

    @staticmethod
    def update_autoswitch_status_sensor(sensor: Sensor, enabled: bool) -> None:
        """Update autoswitch status sensor."""
        sensor.attributes[Attributes.STATE] = States.ON
        sensor.attributes[Attributes.VALUE] = "ON" if enabled else "OFF"

    @staticmethod
    def update_colorspace_sensor(sensor: Sensor, mode: str) -> None:
        """Update color space sensor."""
        sensor.attributes[Attributes.STATE] = States.ON
        sensor.attributes[Attributes.VALUE] = mode

    @staticmethod
    def update_deep_color_sensor(sensor: Sensor, mode: str) -> None:
        """Update deep color sensor."""
        sensor.attributes[Attributes.STATE] = States.ON
        sensor.attributes[Attributes.VALUE] = mode

    @staticmethod
    def update_audio_tx0_sensor(sensor: Sensor, audio_info: str) -> None:
        """Update audio TX0 sensor."""
        sensor.attributes[Attributes.STATE] = States.ON
        sensor.attributes[Attributes.VALUE] = audio_info

    @staticmethod
    def update_audio_tx1_sensor(sensor: Sensor, audio_info: str) -> None:
        """Update audio TX1 sensor."""
        sensor.attributes[Attributes.STATE] = States.ON
        sensor.attributes[Attributes.VALUE] = audio_info

    @staticmethod
    def update_audio_out_sensor(sensor: Sensor, audio_info: str) -> None:
        """Update audio out sensor."""
        sensor.attributes[Attributes.STATE] = States.ON
        sensor.attributes[Attributes.VALUE] = audio_info

    @staticmethod
    def update_video_input_sensor(sensor: Sensor, video_info: str) -> None:
        """Update video input sensor."""
        sensor.attributes[Attributes.STATE] = States.ON
        sensor.attributes[Attributes.VALUE] = video_info

    @staticmethod
    def update_video_tx0_sensor(sensor: Sensor, video_info: str) -> None:
        """Update video TX0 sensor."""
        sensor.attributes[Attributes.STATE] = States.ON
        sensor.attributes[Attributes.VALUE] = video_info

    @staticmethod
    def update_video_tx1_sensor(sensor: Sensor, video_info: str) -> None:
        """Update video TX1 sensor."""
        sensor.attributes[Attributes.STATE] = States.ON
        sensor.attributes[Attributes.VALUE] = video_info

    @staticmethod
    def update_sink_tx0_sensor(sensor: Sensor, sink_info: str) -> None:
        """Update sink TX0 sensor."""
        sensor.attributes[Attributes.STATE] = States.ON
        sensor.attributes[Attributes.VALUE] = sink_info

    @staticmethod
    def update_sink_tx1_sensor(sensor: Sensor, sink_info: str) -> None:
        """Update sink TX1 sensor."""
        sensor.attributes[Attributes.STATE] = States.ON
        sensor.attributes[Attributes.VALUE] = sink_info
