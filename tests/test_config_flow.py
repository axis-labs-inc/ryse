"""Tests for the RYSE BLE config flow."""

from __future__ import annotations

from unittest.mock import MagicMock

from bleak.exc import BleakError
import pytest

from homeassistant.components.ryse.const import DOMAIN
from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_USER
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    DEVICE_ADDRESS,
    DEVICE_NAME,
    IDLE_MANUFACTURER_DATA,
    RYSE_SERVICE_INFO,
    make_service_info,
)

from tests.common import MockConfigEntry
from tests.components.bluetooth import inject_bluetooth_service_info_bleak

USER_INPUT = {CONF_ADDRESS: DEVICE_ADDRESS}

PAIRING_ERRORS = [
    (Exception("boom"), "unexpected_error"),
    (TimeoutError("timeout"), "cannot_connect"),
    (OSError("os error"), "cannot_connect"),
    (BleakError("bleak error"), "cannot_connect"),
    (False, "cannot_connect"),
]


@pytest.mark.usefixtures("discovered_device")
async def test_async_step_user_success(
    hass: HomeAssistant, mock_device: MagicMock
) -> None:
    """Test user flow succeeds and creates entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEVICE_NAME
    assert result["data"] == {}
    assert result["result"].unique_id == DEVICE_ADDRESS
    mock_device.pair.assert_awaited_once()
    mock_device.disconnect.assert_awaited_once()


@pytest.mark.parametrize(("pair_result", "expected_error"), PAIRING_ERRORS)
@pytest.mark.usefixtures("discovered_device")
async def test_async_step_user_errors(
    hass: HomeAssistant,
    mock_device: MagicMock,
    pair_result: Exception | bool,
    expected_error: str,
) -> None:
    """Test errors during user pairing can be recovered from."""
    mock_device.pair.side_effect = [pair_result, True]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": expected_error}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEVICE_NAME
    assert result["data"] == {}
    assert result["result"].unique_id == DEVICE_ADDRESS


@pytest.mark.usefixtures("discovered_device")
async def test_async_step_user_device_added_between_steps(
    hass: HomeAssistant,
) -> None:
    """Test that we abort if the device gets added in another flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DEVICE_ADDRESS,
        data={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_async_step_user_no_devices_found(hass: HomeAssistant) -> None:
    """Test that we abort when no devices are discovered."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


@pytest.mark.usefixtures("discovered_device")
async def test_async_step_user_skips_already_configured(hass: HomeAssistant) -> None:
    """Test that we skip already configured devices in user flow discovery."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DEVICE_ADDRESS,
        data={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_async_step_user_skips_non_pairing_device(hass: HomeAssistant) -> None:
    """Test that we skip devices that are not advertising pairing mode."""
    inject_bluetooth_service_info_bleak(
        hass, make_service_info(manufacturer_data=IDLE_MANUFACTURER_DATA)
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_async_step_user_skips_non_ryse_device(hass: HomeAssistant) -> None:
    """Test that we skip devices from other manufacturers."""
    inject_bluetooth_service_info_bleak(
        hass,
        make_service_info(
            address="11:22:33:44:55:66",
            name="Generic Device",
            manufacturer_data={999: b"\xcc"},
            service_uuids=["00001234-0000-1000-8000-00805f9b34fb"],
        ),
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_async_step_bluetooth(
    hass: HomeAssistant, mock_device: MagicMock
) -> None:
    """Test Bluetooth discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=RYSE_SERVICE_INFO,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEVICE_NAME
    assert result["data"] == {}
    assert result["result"].unique_id == DEVICE_ADDRESS
    mock_device.pair.assert_awaited_once()


@pytest.mark.parametrize(("pair_result", "expected_error"), PAIRING_ERRORS)
async def test_async_step_bluetooth_errors(
    hass: HomeAssistant,
    mock_device: MagicMock,
    pair_result: Exception | bool,
    expected_error: str,
) -> None:
    """Test Bluetooth discovery confirm errors can be recovered from."""
    mock_device.pair.side_effect = [pair_result, True]

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=RYSE_SERVICE_INFO,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": expected_error}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEVICE_NAME
    assert result["data"] == {}
    assert result["result"].unique_id == DEVICE_ADDRESS


async def test_async_step_bluetooth_already_configured(hass: HomeAssistant) -> None:
    """Test abort if device already configured before bluetooth discovery."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DEVICE_ADDRESS,
        data={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=RYSE_SERVICE_INFO,
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_async_step_bluetooth_not_in_pairing_mode(
    hass: HomeAssistant, mock_device: MagicMock
) -> None:
    """Test we refuse to pair when the shade is not advertising pairing mode."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=make_service_info(manufacturer_data=IDLE_MANUFACTURER_DATA),
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "not_in_pairing_mode"}
    mock_device.pair.assert_not_called()


async def test_async_step_bluetooth_fallback_name(hass: HomeAssistant) -> None:
    """Test the discovery flow falls back to a generic name."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=make_service_info(name=""),
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"
    assert result["description_placeholders"] == {"name": "RYSE device"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "RYSE device"
    assert result["data"] == {}
    assert result["result"].unique_id == DEVICE_ADDRESS
