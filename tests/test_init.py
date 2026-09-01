"""Tests for RYSE init setup."""

from unittest.mock import MagicMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import DEVICE_ADDRESS, make_service_info

from tests.common import MockConfigEntry
from tests.components.bluetooth import inject_bluetooth_service_info_bleak


async def test_setup_and_unload(
    hass: HomeAssistant,
    mock_device: MagicMock,
    setup_integration: MockConfigEntry,
) -> None:
    """Test integration setup and unload."""
    assert setup_integration.state is ConfigEntryState.LOADED

    await hass.config_entries.async_unload(setup_integration.entry_id)
    await hass.async_block_till_done()

    assert setup_integration.state is ConfigEntryState.NOT_LOADED
    mock_device.disconnect.assert_awaited_once()


async def test_setup_without_ble_device(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test setup is retried when the device is not seen by the bluetooth stack."""
    with patch(
        "homeassistant.components.ryse.async_ble_device_from_address",
        return_value=None,
    ):
        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_ble_device_updated_on_advertisement(
    hass: HomeAssistant,
    mock_device: MagicMock,
    setup_integration: MockConfigEntry,
) -> None:
    """Test a new advertisement refreshes the route to the device."""
    mock_device.set_ble_device.reset_mock()

    inject_bluetooth_service_info_bleak(hass, make_service_info(rssi=-30))
    await hass.async_block_till_done()

    mock_device.set_ble_device.assert_called_once()
    assert mock_device.set_ble_device.call_args[0][0].address == DEVICE_ADDRESS


async def test_ble_device_not_updated_after_unload(
    hass: HomeAssistant,
    mock_device: MagicMock,
    setup_integration: MockConfigEntry,
) -> None:
    """Test the advertisement subscription is dropped when the entry unloads."""
    await hass.config_entries.async_unload(setup_integration.entry_id)
    await hass.async_block_till_done()
    mock_device.set_ble_device.reset_mock()

    inject_bluetooth_service_info_bleak(hass, make_service_info(rssi=-30))
    await hass.async_block_till_done()

    mock_device.set_ble_device.assert_not_called()
