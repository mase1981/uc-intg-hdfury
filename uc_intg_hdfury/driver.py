"""
HDFury driver.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging

from ucapi_framework import BaseIntegrationDriver

from uc_intg_hdfury.config import HDFuryConfig
from uc_intg_hdfury.device import HDFuryDevice
from uc_intg_hdfury.remote import HDFuryRemote
from uc_intg_hdfury.sensor import create_sensors
from uc_intg_hdfury.select_entities import create_select_entities

_LOG = logging.getLogger(__name__)


class HDFuryDriver(BaseIntegrationDriver[HDFuryDevice, HDFuryConfig]):
    """HDFury integration driver."""

    def __init__(self):
        super().__init__(
            device_class=HDFuryDevice,
            entity_classes=[
                HDFuryRemote,
                lambda cfg, dev: create_sensors(cfg, dev),
                lambda cfg, dev: create_select_entities(cfg, dev),
            ],
            driver_id="uc-intg-hdfury",
            require_connection_before_registry=True,
        )
