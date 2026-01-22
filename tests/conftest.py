"""
Pytest Configuration and Fixtures

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""
import asyncio
import pytest
import logging


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_logger():
    """Create a mock logger for tests."""
    logger = logging.getLogger("test")
    logger.setLevel(logging.DEBUG)
    return logger


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration after each test."""
    yield
    logging.getLogger().handlers = []
