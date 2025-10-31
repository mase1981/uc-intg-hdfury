"""
HDFury Integration for Unfolded Circle Remote Two/3.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""
import json
import logging
import os
from dataclasses import asdict, dataclass
from typing import Callable

log = logging.getLogger(__name__)

@dataclass
class HDFuryDeviceConfig:
    identifier: str
    name: str
    host: str
    port: int
    model_id: str = "vrroom"

class Devices:
    def __init__(self, config_dir: str, on_add: Callable | None, on_remove: Callable | None):
        self.config_dir = config_dir
        self.config_file_path = os.path.join(config_dir, "config.json")
        self._on_add = on_add
        self._on_remove = on_remove
        self.devices: dict[str, HDFuryDeviceConfig] = {}
        self.load()

    def load(self):
        if not os.path.exists(self.config_file_path): return
        log.info("Loading device configurations from %s", self.config_file_path)
        try:
            with open(self.config_file_path, 'r') as f:
                devices_json = json.load(f)
                for identifier, dev_json in devices_json.items():
                    if 'model_id' not in dev_json:
                        dev_json['model_id'] = 'vrroom'
                    self.devices[identifier] = HDFuryDeviceConfig(**dev_json)
        except (json.JSONDecodeError, TypeError):
            log.error("Could not decode config.json. Starting fresh.")
            os.remove(self.config_file_path)
    
    def save(self):
        log.info("Saving device configurations to %s", self.config_file_path)
        with open(self.config_file_path, 'w') as f:
            json.dump({k: asdict(v) for k, v in self.devices.items()}, f, indent=2)

    def add(self, device: HDFuryDeviceConfig):
        if device.identifier in self.devices: return
        self.devices[device.identifier] = device
        self.save()
        if self._on_add: self._on_add(device)

    def all(self) -> list[HDFuryDeviceConfig]:
        return list(self.devices.values())