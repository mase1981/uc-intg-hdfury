"""
HDFury Integration for Unfolded Circle Remote Two/3.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""
import asyncio
import logging
import ucapi
from ucapi import media_player, DeviceStates, api_definitions
from ucapi.remote import States as RemoteStates
from ucapi.select import Attributes as SelectAttributes
from uc_intg_hdfury.device import HDFuryDevice, EVENTS
from uc_intg_hdfury.config import Devices, HDFuryDeviceConfig
from uc_intg_hdfury.hdfury_client import HDFuryClient
from uc_intg_hdfury.models import MODEL_CONFIGS, get_model_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)
loop = asyncio.get_event_loop()
api = ucapi.api.IntegrationAPI(loop=loop)
configured_devices: dict[str, HDFuryDevice] = {}
devices_config: Devices | None = None

async def driver_setup_handler(request: ucapi.SetupDriver) -> ucapi.SetupAction:
    if isinstance(request, ucapi.DriverSetupRequest):
        return ucapi.RequestUserInput(
            title={"en": "Select HDFury Device Model"},
            settings=[
                {
                    "id": "model",
                    "label": {"en": "Device Model"},
                    "field": {
                        "dropdown": {
                            "value": "vrroom",
                            "items": [
                                {"id": "vrroom", "label": {"en": "VRRooM"}},
                                {"id": "vertex2", "label": {"en": "VERTEX2"}},
                                {"id": "vertex", "label": {"en": "VERTEX"}},
                                {"id": "diva", "label": {"en": "DIVA"}},
                                {"id": "maestro", "label": {"en": "Maestro"}},
                                {"id": "arcana2", "label": {"en": "ARCANA2"}},
                                {"id": "dr8k", "label": {"en": "Dr.HDMI 8K"}}
                            ]
                        }
                    }
                }
            ]
        )
    if isinstance(request, ucapi.UserDataResponse):
        user_input = request.input_values
        model_id = user_input.get("model", "vrroom")

        if "host" not in user_input:
            model_config = get_model_config(model_id)
            return ucapi.RequestUserInput(
                title={"en": "HDFury Device Address"},
                settings=[
                    {"id": "model", "label": {"en": "Model"}, "field": {"text": {"value": model_id}}},
                    {"id": "host", "label": {"en": "IP Address"}, "field": {"text": {"value": ""}}},
                    {"id": "port", "label": {"en": "Port"}, "field": {"number": {"value": model_config.default_port}}}
                ]
            )

        host = user_input.get("host")
        port = int(user_input.get("port", 2222))
        if not host:
            return ucapi.SetupError("IP address is required.")

        identifier = f"hdfury-{host.replace('.', '-')}"
        if identifier in configured_devices:
            return ucapi.SetupComplete()

        model_config = get_model_config(model_id)

        try:
            log.info(f"Testing connection to {host}:{port}")
            temp_client = HDFuryClient(host, port, log, model_config)
            await temp_client.connect()
            await temp_client.disconnect()
            log.info("Connection test successful, waiting for device to reset...")
            await asyncio.sleep(2.0)

        except Exception as e:
            log.error(f"Connection test failed: {e}")
            return ucapi.SetupError(f"Could not connect to device: {e}")

        log.info(f"Creating device for {host}")
        device = HDFuryDevice(host, port, model_config)

        api.available_entities.add(device.media_player_entity)
        api.available_entities.add(device.remote_entity)
        for sensor_entity in device.sensor_entities:
            api.available_entities.add(sensor_entity)
        for select_entity in device.select_entities:
            api.available_entities.add(select_entity)
        device.events.on(EVENTS.UPDATE, on_device_update)

        try:
            await asyncio.wait_for(device.start(), timeout=15.0)
            if device.state != media_player.States.ON:
                log.warning(f"Device state is {device.state}, but continuing setup")

            configured_devices[identifier] = device
            new_config = HDFuryDeviceConfig(identifier, device.name, host, port, model_id)
            devices_config.add(new_config)
            log.info(f"Device {identifier} added successfully")
            return ucapi.SetupComplete()

        except asyncio.TimeoutError:
            log.error("Device connection timed out during setup")
            configured_devices[identifier] = device
            new_config = HDFuryDeviceConfig(identifier, device.name, host, port, model_id)
            devices_config.add(new_config)
            log.info(f"Device {identifier} added (timeout occurred)")
            return ucapi.SetupComplete()

        except Exception as e:
            log.error(f"Setup error: {e}", exc_info=True)
            return ucapi.SetupError(f"Setup failed: {e}")

    return ucapi.SetupError()

@api.listens_to(api_definitions.Events.CONNECT)
async def on_connect() -> None:
    log.info("Remote connected")

    if devices_config:
        devices_config.load()
        log.debug("Configuration reloaded from disk")

    if configured_devices:
        log.info(f"Devices configured ({len(configured_devices)}), setting driver state to CONNECTED")
        await api.set_device_state(DeviceStates.CONNECTED)
    else:
        log.info("No devices configured yet")
        await api.set_device_state(DeviceStates.DISCONNECTED)

@api.listens_to(api_definitions.Events.DISCONNECT)
async def on_disconnect() -> None:
    log.info("Remote disconnected. Keeping devices running for reconnection.")

@api.listens_to(api_definitions.Events.SUBSCRIBE_ENTITIES)
async def on_subscribe_entities(entity_ids: list[str]):
    log.info(f"Entities subscribed: {entity_ids}")

    device_ids = set()
    for eid in entity_ids:
        parts = eid.replace('-remote', '').replace('-connection', '').replace('-firmware', '')
        parts = parts.replace('-current-input', '').replace('-edid-mode', '').replace('-hdr-mode', '')
        parts = parts.replace('-hdcp-mode', '').replace('-oled-status', '').replace('-autoswitch-status', '')
        parts = parts.replace('-audio-tx0', '').replace('-audio-tx1', '').replace('-audio-out', '')
        parts = parts.replace('-video-input', '').replace('-video-tx0', '').replace('-video-tx1', '')
        parts = parts.replace('-sink-tx0', '').replace('-sink-tx1', '').replace('-input-select', '')
        parts = parts.replace('-edid-mode-select', '').replace('-edid-audio-select', '').replace('-hdcp-select', '')
        parts = parts.replace('-earcforce-select', '').replace('-hdr-select', '').replace('-cecla-select', '')
        parts = parts.replace('-arcforce-select', '').replace('-colorspace', '').replace('-deep-color', '')
        device_ids.add(parts)

    for identifier in device_ids:
        if identifier in configured_devices:
            device = configured_devices[identifier]
            log.info(f"Processing subscription for device {identifier}")

            if not device.client.is_connected():
                log.info(f"Device {identifier} not connected, starting connection...")
                try:
                    await device.start()
                    log.info(f"Device {identifier} connected successfully")
                except Exception as e:
                    log.error(f"Failed to connect device {identifier}: {e}")
            else:
                log.info(f"Device {identifier} already connected")

            push_device_state(device)

@api.listens_to(api_definitions.Events.UNSUBSCRIBE_ENTITIES)
async def on_unsubscribe_entities(entity_ids: list[str]):
    log.info(f"Entities unsubscribed: {entity_ids}")

def on_device_update(device: HDFuryDevice):
    push_device_state(device)

def push_device_state(device: HDFuryDevice):
    if mp_entity := device.media_player_entity:
        if api.configured_entities.contains(mp_entity.id):
            mp_attributes = {
                "state": device.state,
                "media_title": device.media_title,
                "media_artist": device.media_artist,
                "media_album": device.media_album,
                "source_list": device.source_list,
                "source": device.current_source,
            }
            api.configured_entities.update_attributes(mp_entity.id, mp_attributes)
            log.debug(f"Pushed state to entity {mp_entity.id}: {device.state}")

    if remote_entity := device.remote_entity:
        if api.configured_entities.contains(remote_entity.id):
            remote_attributes = {
                "state": RemoteStates.ON if device.state == media_player.States.ON else RemoteStates.OFF
            }
            api.configured_entities.update_attributes(remote_entity.id, remote_attributes)
            log.debug(f"Pushed state to entity {remote_entity.id}")

    for sensor_entity in device.sensor_entities:
        if api.configured_entities.contains(sensor_entity.id):
            sensor_attributes = {
                "state": sensor_entity.attributes.get("state"),
                "value": sensor_entity.attributes.get("value"),
            }
            api.configured_entities.update_attributes(sensor_entity.id, sensor_attributes)
            log.debug(f"Pushed state to sensor {sensor_entity.id}")

    for select_entity in device.select_entities:
        if api.configured_entities.contains(select_entity.id):
            select_attributes = {
                "state": select_entity.attributes.get(SelectAttributes.STATE),
                "options": select_entity.attributes.get(SelectAttributes.OPTIONS),
                "current_option": select_entity.attributes.get(SelectAttributes.CURRENT_OPTION),
            }
            api.configured_entities.update_attributes(select_entity.id, select_attributes)
            log.debug(f"Pushed state to select {select_entity.id}")

def add_device(device_config: HDFuryDeviceConfig):
    identifier = device_config.identifier
    if identifier in configured_devices:
        log.info(f"Device {identifier} already configured, skipping")
        return

    log.info(f"Adding device from config: {identifier}")
    model_config = get_model_config(device_config.model_id)
    device = HDFuryDevice(device_config.host, device_config.port, model_config)

    api.available_entities.add(device.media_player_entity)
    api.available_entities.add(device.remote_entity)
    for sensor_entity in device.sensor_entities:
        api.available_entities.add(sensor_entity)
    for select_entity in device.select_entities:
        api.available_entities.add(select_entity)
    device.events.on(EVENTS.UPDATE, on_device_update)
    configured_devices[identifier] = device

async def cleanup_on_shutdown():
    log.info("Shutting down HDFury driver...")
    if configured_devices:
        await asyncio.gather(*[d.stop() for d in configured_devices.values()], return_exceptions=True)

async def main():
    global devices_config
    log.info("Starting HDFury driver...")

    devices_config = Devices(api.config_dir_path, add_device, None)
    for device_config in devices_config.all():
        add_device(device_config)

    log.info(f"Loaded {len(configured_devices)} device(s) from config")

    await api.init(driver_path="driver.json", setup_handler=driver_setup_handler)

    log.info("HDFury integration initialized and ready for connections")

if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except (KeyboardInterrupt, asyncio.CancelledError):
        log.info("Driver stopped.")
    finally:
        loop.run_until_complete(cleanup_on_shutdown())
        loop.close()
