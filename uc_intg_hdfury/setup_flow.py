"""
HDFury setup flow.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
import re
from typing import Any

from ucapi import RequestUserInput
from ucapi_framework import BaseSetupFlow

from uc_intg_hdfury.config import HDFuryConfig
from uc_intg_hdfury.models import MODEL_CONFIGS, get_model_config

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

    def _address_form(self, model_id: str, address: str = "", port: int | None = None,
                      error: str = "") -> RequestUserInput:
        model_config = get_model_config(model_id)
        settings: list[dict[str, Any]] = []
        if error:
            settings.append(
                {
                    "id": "error",
                    "label": {"en": ""},
                    "field": {"label": {"value": {"en": f"⚠️ {error}"}}},
                }
            )
        settings += [
            {"id": "model", "label": {"en": "Model"}, "field": {"text": {"value": model_id}}},
            {"id": "address", "label": {"en": "IP Address"}, "field": {"text": {"value": address}}},
            {
                "id": "port",
                "label": {"en": "Port"},
                "field": {"number": {"value": port or model_config.default_port}},
            },
        ]
        return RequestUserInput({"en": "HDFury Device Address"}, settings)

    async def query_device(
        self, input_values: dict[str, Any]
    ) -> HDFuryConfig | RequestUserInput:
        """Process setup input and validate connection."""
        model_id = str(input_values.get("model", "vrroom")).strip()
        if model_id not in MODEL_CONFIGS:
            return self.get_manual_entry_form()

        if "address" not in input_values:
            return self._address_form(model_id)

        address = str(input_values.get("address", "")).strip()
        if not address:
            return self._address_form(model_id, error="IP address is required.")

        try:
            port = int(float(input_values.get("port") or get_model_config(model_id).default_port))
        except (TypeError, ValueError):
            return self._address_form(model_id, address, error="Port must be a number.")
        if not 1 <= port <= 65535:
            return self._address_form(model_id, address, error="Port must be 1-65535.")

        if not await self._test_connection(address, port):
            return self._address_form(
                model_id, address, port, f"Cannot connect to HDFury device at {address}:{port}"
            )

        model_config = get_model_config(model_id)
        identifier = "hdfury_" + re.sub(r"[^a-z0-9]+", "_", address.lower()).strip("_")
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
