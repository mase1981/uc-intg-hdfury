import asyncio
import logging
import ucapi
from ucapi import media_player, DeviceStates, api_definitions
from uc_intg_hdfury.device import HDFuryDevice, EVENTS
from uc_intg_hdfury.config import Devices, HDFuryDeviceConfig
from uc_intg_hdfury.hdfury_client import HDFuryClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)
loop = asyncio.get_event_loop()
api = ucapi.api.IntegrationAPI(loop=loop)
configured_devices: dict[str, HDFuryDevice] = {}
devices_config: Devices | None = None

async def driver_setup_handler(request: ucapi.SetupDriver) -> ucapi.SetupAction:
    if isinstance(request, ucapi.DriverSetupRequest):
        return ucapi.RequestUserInput(
            title={"en": "HDFury Device Address"},
            settings=[
                {"id": "host", "label": {"en": "IP Address"}, "field": {"text": {"value": ""}}},
                {"id": "port", "label": {"en": "Port"}, "field": {"number": {"value": 2222}}}
            ]
        )
    if isinstance(request, ucapi.UserDataResponse):
        user_input = request.input_values
        host, port = user_input.get("host"), int(user_input.get("port", 2222))
        if not host: return ucapi.SetupError("IP address is required.")
        
        identifier = f"hdfury-{host.replace('.', '-')}"
        if identifier in configured_devices: return ucapi.SetupComplete()

        try:
            temp_client = HDFuryClient(host, port, log)
            await temp_client.connect()
            model_name = await temp_client.get_device_name()
            await temp_client.disconnect()
        except Exception as e:
            return ucapi.SetupError(f"Could not connect to get device model: {e}")

        device = HDFuryDevice(host, port, model_name)
        api.available_entities.add(device.media_player_entity)
        api.available_entities.add(device.remote_entity)
        device.events.on(EVENTS.UPDATE, on_device_update)

        # Add small delay to ensure entities are properly registered on slower hardware
        await asyncio.sleep(0.2)

        try:
            await asyncio.wait_for(device.start(), timeout=15.0)
            if device.state != media_player.States.ON:
                 return ucapi.SetupError("Could not get valid status from HDFury.")
            
            configured_devices[identifier] = device
            new_config = HDFuryDeviceConfig(identifier, device.name, host, port)
            devices_config.add(new_config)
            return ucapi.SetupComplete()
        except Exception as e:
            return ucapi.SetupError(f"Connection failed during setup: {e}")
    return ucapi.SetupError()

@api.listens_to(api_definitions.Events.CONNECT)
async def on_connect() -> None:
    log.info("Remote connected. Setting driver state to CONNECTED.")
    await api.set_device_state(DeviceStates.CONNECTED)

@api.listens_to(api_definitions.Events.SUBSCRIBE_ENTITIES)
async def on_subscribe_entities(entity_ids: list[str]):
    all_device_ids = { eid.split('.')[-1].split('-remote')[0] for eid in entity_ids }
    
    for identifier in all_device_ids:
        if identifier in configured_devices:
            device = configured_devices[identifier]
            if not device.client.is_connected(): await device.start()
            push_device_state(device)

def on_device_update(device: HDFuryDevice):
    push_device_state(device)

def push_device_state(device: HDFuryDevice):
    if mp_entity := device.media_player_entity:
        if api.configured_entities.contains(mp_entity.id):
            attributes_to_update = {
                "name": {"en": device.name},
                "state": device.state,
                "media_title": device.media_title,
                "media_artist": device.media_artist,
                "media_album": device.media_album,
                "source_list": device.source_list,
                "source": device.current_source,
            }
            api.configured_entities.update_attributes(mp_entity.id, attributes_to_update)
            log.info(f"Pushed state to entity {mp_entity.id}")

    if remote_entity := device.remote_entity:
        if api.configured_entities.contains(remote_entity.id):
            remote_entity_attributes = {
                "name": f"{device.name} Controls"
            }
            api.configured_entities.update_attributes(remote_entity.id, remote_entity_attributes)
            log.info(f"Pushed state to entity {remote_entity.id}")

def add_device(device_config: HDFuryDeviceConfig):
    identifier = device_config.identifier
    if identifier in configured_devices: return

    device = HDFuryDevice(device_config.host, device_config.port, "VRRoom")
    
    api.available_entities.add(device.media_player_entity)
    api.available_entities.add(device.remote_entity)
    device.events.on(EVENTS.UPDATE, on_device_update)
    configured_devices[identifier] = device

async def main():
    global devices_config
    log.info("Starting HDFury driver...")
    
    devices_config = Devices(api.config_dir_path, add_device, None)
    for device_config in devices_config.all():
        add_device(device_config)
    
    # Add small delay to ensure entities are properly registered before API init
    if configured_devices:
        await asyncio.sleep(0.5)
    
    await api.init(driver_path="driver.json", setup_handler=driver_setup_handler)
    
    if configured_devices:
        log.info(f"Starting connection tasks for {len(configured_devices)} configured device(s).")
        # Add small delay before starting device connections to ensure API is fully ready
        await asyncio.sleep(0.3)
        await asyncio.gather(*[d.start() for d in configured_devices.values()])
    
if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except (KeyboardInterrupt, asyncio.CancelledError):
        log.info("Driver stopped.")
    finally:
        if configured_devices:
            loop.run_until_complete(asyncio.gather(*[d.stop() for d in configured_devices.values()]))
        loop.close()