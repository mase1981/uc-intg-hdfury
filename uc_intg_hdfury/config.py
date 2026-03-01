"""
HDFury configuration for Unfolded Circle integration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from dataclasses import dataclass


@dataclass
class HDFuryConfig:
    """HDFury device configuration."""

    identifier: str
    name: str
    address: str
    port: int
    model_id: str = "vrroom"
