"""
HDFury Integration for Unfolded Circle Remote.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import json
import logging
import os
from pathlib import Path

from ucapi import DeviceStates
from ucapi_framework import BaseConfigManager, get_config_path

from uc_intg_hdfury.config import HDFuryConfig
from uc_intg_hdfury.driver import HDFuryDriver
from uc_intg_hdfury.setup_flow import HDFurySetupFlow

try:
    driver_path = Path(__file__).parent.parent.absolute() / "driver.json"
    with open(driver_path, "r", encoding="utf-8") as f:
        __version__ = json.load(f).get("version", "0.0.0")
except (FileNotFoundError, json.JSONDecodeError):
    __version__ = "0.0.0"

_LOG = logging.getLogger(__name__)


async def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    )

    _LOG.info("Starting HDFury Integration v%s", __version__)

    driver = HDFuryDriver()

    config_path = get_config_path(driver.api.config_dir_path or "")
    config_manager = BaseConfigManager(
        config_path,
        add_handler=driver.on_device_added,
        remove_handler=driver.on_device_removed,
        config_class=HDFuryConfig,
    )
    driver.config_manager = config_manager

    setup_handler = HDFurySetupFlow.create_handler(driver)
    driver_json_path = os.path.join(os.path.dirname(__file__), "..", "driver.json")
    await driver.api.init(os.path.abspath(driver_json_path), setup_handler)

    await driver.register_all_device_instances(connect=False)

    device_count = len(list(config_manager.all()))
    if device_count > 0:
        await driver.api.set_device_state(DeviceStates.CONNECTED)
    else:
        await driver.api.set_device_state(DeviceStates.DISCONNECTED)

    _LOG.info("HDFury integration started")

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
