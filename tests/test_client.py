"""
Tests for HDFury Client

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""
import asyncio
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uc_intg_hdfury.hdfury_client import HDFuryClient, HDFuryConnectionError, HDFuryCommandError
from uc_intg_hdfury.models import VRROOM_CONFIG


@pytest.fixture
def mock_logger():
    return logging.getLogger("test")


@pytest.fixture
def client(mock_logger):
    return HDFuryClient("192.168.1.100", 2222, mock_logger, VRROOM_CONFIG)


@pytest.mark.asyncio
async def test_client_connection(client, mock_logger):
    """Test client connection establishes successfully."""
    with patch("asyncio.open_connection") as mock_open:
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.is_closing.return_value = False
        mock_reader.read.return_value = b"Welcome\r\n"
        mock_open.return_value = (mock_reader, mock_writer)

        await client.connect()

        assert client.is_connected()
        mock_open.assert_called_once_with("192.168.1.100", 2222)


@pytest.mark.asyncio
async def test_client_disconnect(client):
    """Test client disconnects cleanly."""
    client._writer = MagicMock()
    client._writer.wait_closed = AsyncMock()

    await client.disconnect()

    client._writer.close.assert_called_once()
    assert not client.is_connected()


@pytest.mark.asyncio
async def test_send_command_success(client):
    """Test successful command execution."""
    client._writer = MagicMock()
    client._writer.is_closing.return_value = False
    client._writer.drain = AsyncMock()
    client._reader = AsyncMock()
    client._reader.readline.return_value = b"OK\r\n"

    response = await client.send_command("get ver")

    assert response == "OK"
    client._writer.write.assert_called_once()


@pytest.mark.asyncio
async def test_send_command_timeout_retry(client):
    """Test command retry on timeout."""
    client._writer = MagicMock()
    client._writer.is_closing.return_value = False
    client._writer.drain = AsyncMock()
    client._reader = AsyncMock()
    client._reader.readline.side_effect = [asyncio.TimeoutError(), b"OK\r\n"]
    client.disconnect = AsyncMock()
    client._ensure_connection = AsyncMock()

    response = await client.send_command("get ver")

    assert response == "OK"
    assert client.disconnect.call_count == 1


@pytest.mark.asyncio
async def test_reboot_command(client):
    """Test reboot command sends correct format."""
    client.send_command = AsyncMock(return_value="OK")

    await client.reboot()

    client.send_command.assert_called_once_with("set reboot")


@pytest.mark.asyncio
async def test_factory_reset_valid_modes(client):
    """Test factory reset accepts valid modes (1, 2, 3)."""
    client.send_command = AsyncMock(return_value="OK")

    for mode in [1, 2, 3]:
        await client.factory_reset(mode)

    assert client.send_command.call_count == 3


@pytest.mark.asyncio
async def test_factory_reset_invalid_mode(client):
    """Test factory reset raises error for invalid mode."""
    with pytest.raises(HDFuryCommandError):
        await client.factory_reset(4)


@pytest.mark.asyncio
async def test_hotplug_command(client):
    """Test hotplug command sends correct format."""
    client.send_command = AsyncMock(return_value="OK")

    await client.hotplug()

    client.send_command.assert_called_once_with("set hotplug")


@pytest.mark.asyncio
async def test_mute_tx_audio(client):
    """Test mute TX audio commands."""
    client.send_command = AsyncMock(return_value="OK")

    await client.mute_tx_audio(0, True)
    client.send_command.assert_called_with("set mutetx0audio on")

    await client.mute_tx_audio(1, False)
    client.send_command.assert_called_with("set mutetx1audio off")


@pytest.mark.asyncio
async def test_analog_volume_range(client):
    """Test analog volume respects -30 to +10 range."""
    client.send_command = AsyncMock(return_value="OK")

    await client.set_analog_volume(-30)
    client.send_command.assert_called_with("set analogvolume -30")

    await client.set_analog_volume(10)
    client.send_command.assert_called_with("set analogvolume 10")

    await client.set_analog_volume(-50)
    client.send_command.assert_called_with("set analogvolume -30")

    await client.set_analog_volume(20)
    client.send_command.assert_called_with("set analogvolume 10")


@pytest.mark.asyncio
async def test_analog_bass_range(client):
    """Test analog bass respects -10 to +10 range."""
    client.send_command = AsyncMock(return_value="OK")

    await client.set_analog_bass(-10)
    client.send_command.assert_called_with("set analogbass -10")

    await client.set_analog_bass(10)
    client.send_command.assert_called_with("set analogbass 10")


@pytest.mark.asyncio
async def test_analog_treble_range(client):
    """Test analog treble respects -10 to +10 range."""
    client.send_command = AsyncMock(return_value="OK")

    await client.set_analog_treble(-10)
    client.send_command.assert_called_with("set analogtreble -10")

    await client.set_analog_treble(10)
    client.send_command.assert_called_with("set analogtreble 10")


@pytest.mark.asyncio
async def test_tx_plus5_commands(client):
    """Test TX plus5 voltage control commands."""
    client.send_command = AsyncMock(return_value="OK")

    await client.set_tx_plus5(0, True)
    client.send_command.assert_called_with("set tx0plus5 on")

    await client.set_tx_plus5(1, False)
    client.send_command.assert_called_with("set tx1plus5 off")


@pytest.mark.asyncio
async def test_htpc_mode_commands(client):
    """Test HTPC mode commands."""
    client.send_command = AsyncMock(return_value="OK")

    await client.set_htpc_mode(0, True)
    client.send_command.assert_called_with("set htpcmode0 on")

    await client.set_htpc_mode(3, False)
    client.send_command.assert_called_with("set htpcmode3 off")


@pytest.mark.asyncio
async def test_oled_page_range(client):
    """Test OLED page respects 0-4 range."""
    client.send_command = AsyncMock(return_value="OK")

    await client.set_oled_page(0)
    client.send_command.assert_called_with("set oledpage 0")

    await client.set_oled_page(4)
    client.send_command.assert_called_with("set oledpage 4")

    await client.set_oled_page(10)
    client.send_command.assert_called_with("set oledpage 4")


@pytest.mark.asyncio
async def test_oled_fade_range(client):
    """Test OLED fade respects 0-255 range."""
    client.send_command = AsyncMock(return_value="OK")

    await client.set_oled_fade(0)
    client.send_command.assert_called_with("set oledfade 0")

    await client.set_oled_fade(255)
    client.send_command.assert_called_with("set oledfade 255")

    await client.set_oled_fade(300)
    client.send_command.assert_called_with("set oledfade 255")


@pytest.mark.asyncio
async def test_cec_logical_address(client):
    """Test CEC logical address commands."""
    client.send_command = AsyncMock(return_value="OK")

    await client.set_cec_logical_address("video")
    client.send_command.assert_called_with("set cecla video")

    await client.set_cec_logical_address("audio")
    client.send_command.assert_called_with("set cecla audio")


@pytest.mark.asyncio
async def test_avi_custom_commands(client):
    """Test AVI custom commands."""
    client.send_command = AsyncMock(return_value="OK")

    await client.set_avi_custom(True)
    client.send_command.assert_called_with("set avicustom on")

    await client.set_avi_custom(False)
    client.send_command.assert_called_with("set avicustom off")


@pytest.mark.asyncio
async def test_avi_disable_commands(client):
    """Test AVI disable commands."""
    client.send_command = AsyncMock(return_value="OK")

    await client.set_avi_disable(True)
    client.send_command.assert_called_with("set avidisable on")

    await client.set_avi_disable(False)
    client.send_command.assert_called_with("set avidisable off")


@pytest.mark.asyncio
async def test_set_source(client):
    """Test set source command."""
    client.send_command = AsyncMock(return_value="OK")

    await client.set_source("HDMI 1")
    client.send_command.assert_called_with("set inseltx0 1")


@pytest.mark.asyncio
async def test_heartbeat_success(client):
    """Test heartbeat returns True on success."""
    client.send_command = AsyncMock(return_value="OK")

    result = await client.heartbeat()

    assert result is True


@pytest.mark.asyncio
async def test_heartbeat_failure(client):
    """Test heartbeat returns False on failure."""
    client.send_command = AsyncMock(side_effect=Exception("Connection lost"))

    result = await client.heartbeat()

    assert result is False
