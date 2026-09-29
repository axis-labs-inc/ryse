"""The RYSE integration."""

import logging

from bleak import BleakError
from bleak.backends.device import BLEDevice
from ryseble.device import RyseBLEDevice

from homeassistant.components.bluetooth import (
    BluetoothCallbackMatcher,
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_register_callback,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady

from .helpers import async_local_scanner_devices

_LOGGER = logging.getLogger(__name__)

type RyseConfigEntry = ConfigEntry[RyseBLEDevice]

PLATFORMS = [Platform.COVER]


async def _async_unpair(device: RyseBLEDevice) -> None:
    """Release the BLE connection, ignoring teardown errors.

    Teardown must not replace a pairing/setup failure: the BLE link is often
    already gone, and the original error is what setup should retry on.
    """
    try:
        await device.unpair()
    except Exception:
        _LOGGER.debug("Error while releasing RYSE connection", exc_info=True)


def _async_local_ble_device(hass: HomeAssistant, address: str) -> BLEDevice | None:
    """Return the BLEDevice seen by a local adapter, ignoring Bluetooth proxies."""
    devices = async_local_scanner_devices(hass, address)
    return devices[0].ble_device if devices else None


async def async_setup_entry(hass: HomeAssistant, entry: RyseConfigEntry) -> bool:
    """Set up RYSE."""
    address = entry.unique_id
    assert address is not None

    from .config_flow import _async_cancel_local_waiter

    _async_cancel_local_waiter(hass, address)

    ble_device = _async_local_ble_device(hass, address)
    if not ble_device:
        raise ConfigEntryNotReady(
            f"Could not find RYSE device with address {address} on a local "
            "Bluetooth adapter"
        )

    device = RyseBLEDevice(ble_device)
    try:
        if not await device.pair():
            await _async_unpair(device)
            raise ConfigEntryNotReady(
                f"Could not connect to RYSE device with address {address}"
            )
    except (TimeoutError, OSError, EOFError, BleakError) as err:
        await _async_unpair(device)
        raise ConfigEntryNotReady(
            f"Could not connect to RYSE device with address {address}"
        ) from err

    entry.runtime_data = device
    entry.async_on_unload(device.unpair)

    @callback
    def _async_update_ble_device(
        service_info: BluetoothServiceInfoBleak,
        change: BluetoothChange,
    ) -> None:
        """Refresh the BLEDevice from a local adapter, ignoring Bluetooth proxies.

        Local adapters set ``service_info.source`` to the adapter MAC, not
        ``SOURCE_LOCAL``. Resolve via scanners that currently see the address.
        """
        ble_device = _async_local_ble_device(hass, service_info.address)
        if ble_device is None:
            return
        device.set_ble_device(ble_device)

    entry.async_on_unload(
        async_register_callback(
            hass,
            _async_update_ble_device,
            BluetoothCallbackMatcher(address=address, connectable=True),
            BluetoothScanningMode.PASSIVE,
        )
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: RyseConfigEntry) -> bool:
    """Unload a RYSE config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
