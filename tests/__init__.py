"""Tests for RYSE BLE integration."""

import time

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

from tests.components.bluetooth import generate_advertisement_data, generate_ble_device

DEVICE_ADDRESS = "AA:BB:CC:DD:EE:FF"
DEVICE_NAME = "RYSE Shade"
SERVICE_UUID = "a72f2800-b0bd-498b-b4cd-4a3901388238"
MANUFACTURER_ID = 1033

# RYSE devices set bit 0x40 of the first manufacturer data byte while the PAIR
# button is held.
PAIRING_MANUFACTURER_DATA = {MANUFACTURER_ID: b"\xcc\x64\x62\x64"}
IDLE_MANUFACTURER_DATA = {MANUFACTURER_ID: b"\x8c\x64\x62\x64"}


def make_service_info(
    address: str = DEVICE_ADDRESS,
    name: str = DEVICE_NAME,
    manufacturer_data: dict[int, bytes] | None = None,
    service_uuids: list[str] | None = None,
    rssi: int = -40,
) -> BluetoothServiceInfoBleak:
    """Build a BluetoothServiceInfoBleak for a RYSE device."""
    manufacturer_data = (
        PAIRING_MANUFACTURER_DATA if manufacturer_data is None else manufacturer_data
    )
    service_uuids = [SERVICE_UUID] if service_uuids is None else service_uuids

    return BluetoothServiceInfoBleak(
        name=name,
        address=address,
        rssi=rssi,
        manufacturer_data=manufacturer_data,
        service_data={},
        service_uuids=service_uuids,
        source="local",
        device=generate_ble_device(address, name),
        advertisement=generate_advertisement_data(
            local_name=name,
            manufacturer_data=manufacturer_data,
            service_uuids=service_uuids,
        ),
        time=time.monotonic(),
        connectable=True,
        tx_power=-127,
    )


RYSE_SERVICE_INFO = make_service_info()
