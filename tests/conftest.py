"""Fixtures for the RYSE integration tests."""

from collections.abc import Callable, Generator
from unittest.mock import AsyncMock, MagicMock, patch

from bleak.backends.device import BLEDevice
import pytest

from homeassistant.components.ryse.const import DOMAIN
from homeassistant.core import HomeAssistant

from . import DEVICE_ADDRESS, DEVICE_NAME, RYSE_SERVICE_INFO

from tests.common import MockConfigEntry
from tests.components.bluetooth import (
    generate_ble_device,
    inject_bluetooth_service_info_bleak,
)


@pytest.fixture(autouse=True)
def mock_bluetooth(enable_bluetooth: None) -> None:
    """Auto mock bluetooth."""


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Device",
        unique_id=DEVICE_ADDRESS,
        data={},
    )


def _subscription(
    callbacks: list[Callable],
) -> Callable[[Callable], Callable[[], None]]:
    """Mimic the library's register/unregister callback contract."""

    def _register(callback: Callable) -> Callable[[], None]:
        callbacks.append(callback)
        return lambda: callbacks.remove(callback)

    return _register


@pytest.fixture
def mock_device() -> MagicMock:
    """Return a mocked RyseBLEDevice."""
    device = MagicMock()
    device.address = DEVICE_ADDRESS
    device.name = DEVICE_NAME
    device.is_connected = False
    device.position = None
    device.is_valid_position.return_value = True
    device.get_real_position.side_effect = lambda position: 100 - position
    device.is_closed.side_effect = lambda position: position == 100
    device.connect = AsyncMock(return_value=True)
    device.pair = AsyncMock(return_value=True)
    device.disconnect = AsyncMock()
    device.send_open = AsyncMock()
    device.send_close = AsyncMock()
    device.send_set_position = AsyncMock()
    device.send_get_position = AsyncMock()

    device.position_callbacks = []
    device.disconnected_callbacks = []
    device.register_position_callback.side_effect = _subscription(
        device.position_callbacks
    )
    device.register_disconnected_callback.side_effect = _subscription(
        device.disconnected_callbacks
    )

    return device


@pytest.fixture(autouse=True)
def mock_ryse_ble_device(mock_device: MagicMock) -> Generator[MagicMock]:
    """Patch RyseBLEDevice so tests never touch real BLE hardware."""
    with (
        patch(
            "homeassistant.components.ryse.RyseBLEDevice",
            return_value=mock_device,
        ),
        patch(
            "homeassistant.components.ryse.config_flow.RyseBLEDevice",
            return_value=mock_device,
        ),
    ):
        yield mock_device


@pytest.fixture
def discovered_device(hass: HomeAssistant) -> None:
    """Make the bluetooth stack aware of the RYSE device."""
    inject_bluetooth_service_info_bleak(hass, RYSE_SERVICE_INFO)


@pytest.fixture
def mock_ble_device() -> Generator[BLEDevice]:
    """Patch the bluetooth lookup so the device is always reachable."""
    ble_device = generate_ble_device(DEVICE_ADDRESS, DEVICE_NAME)
    with patch(
        "homeassistant.components.ryse.async_ble_device_from_address",
        return_value=ble_device,
    ):
        yield ble_device


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant,
    mock_ble_device: BLEDevice,
    mock_config_entry: MockConfigEntry,
) -> MockConfigEntry:
    """Set up the RYSE integration and return its config entry."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    return mock_config_entry
