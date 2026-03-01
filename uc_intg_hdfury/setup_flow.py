"""
HDFury setup flow.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any

from ucapi import RequestUserInput
from ucapi_framework import BaseSetupFlow

from uc_intg_hdfury.config import HDFuryConfig
from uc_intg_hdfury.models import get_model_config

_LOG = logging.getLogger(__name__)


class HDFurySetupFlow(BaseSetupFlow[HDFuryConfig]):
    """Setup flow for HDFury integration."""

    def get_manual_entry_form(self) -> RequestUserInput:
        """Return model selection form as initial setup step."""
        return RequestUserInput(
            {"en": "Select HDFury Device Model"},
            [
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
                                {"id": "dr8k", "label": {"en": "Dr.HDMI 8K"}},
                            ],
                        }
                    },
                }
            ],
        )

    async def query_device(
        self, input_values: dict[str, Any]
    ) -> HDFuryConfig | RequestUserInput:
        """Process setup input and validate connection."""
        model_id = input_values.get("model", "vrroom")

        if "address" not in input_values:
            model_config = get_model_config(model_id)
            return RequestUserInput(
                {"en": "HDFury Device Address"},
                [
                    {
                        "id": "model",
                        "label": {"en": "Model"},
                        "field": {"text": {"value": model_id}},
                    },
                    {
                        "id": "address",
                        "label": {"en": "IP Address"},
                        "field": {"text": {"value": ""}},
                    },
                    {
                        "id": "port",
                        "label": {"en": "Port"},
                        "field": {"number": {"value": model_config.default_port}},
                    },
                ],
            )

        address = input_values.get("address", "").strip()
        if not address:
            raise ValueError("IP address is required")

        port = int(input_values.get("port", 2222))
        model_config = get_model_config(model_id)

        if not await self._test_connection(address, port):
            raise ValueError(f"Cannot connect to HDFury device at {address}:{port}")

        identifier = f"hdfury_{address.replace('.', '_')}"
        name = f"HDFury {model_config.display_name}"

        _LOG.info("Setup complete for %s at %s:%d", name, address, port)

        return HDFuryConfig(
            identifier=identifier,
            name=name,
            address=address,
            port=port,
            model_id=model_id,
        )

    async def _test_connection(self, address: str, port: int) -> bool:
        """Test TCP connection to HDFury device."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(address, port),
                timeout=5.0,
            )

            try:
                await asyncio.wait_for(reader.read(2048), timeout=1.0)
            except asyncio.TimeoutError:
                pass

            writer.write(b"get ver\r\n")
            await writer.drain()

            try:
                response = await asyncio.wait_for(reader.readline(), timeout=3.0)
                _LOG.info("HDFury response: %s", response.decode("ascii", errors="ignore").strip())
            except asyncio.TimeoutError:
                pass

            writer.close()
            await writer.wait_closed()
            return True

        except Exception as err:
            _LOG.warning("Connection test failed: %s", err)
            return False
