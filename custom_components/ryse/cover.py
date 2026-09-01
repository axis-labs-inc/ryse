"""Support for RYSE Smart Shades via BLE."""

import logging
from typing import Any

from bleak import BleakError
from ryseble import RyseBLEDevice

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import RyseConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RyseConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up RYSE Smart Shade cover from a config entry."""
    async_add_entities([RyseCoverEntity(entry.runtime_data, entry)])


class RyseCoverEntity(CoverEntity):
    """Representation of a RYSE Smart Shade BLE cover entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(self, device: RyseBLEDevice, config_entry: RyseConfigEntry) -> None:
        """Initialize the Smart Shade cover entity."""
        self._device = device

        self._attr_unique_id = f"{device.address}_cover"
        self._current_position: int | None = None
        self._attr_is_closed: bool | None = None
        self._attr_available: bool = False
        self._attr_device_info = DeviceInfo(
            manufacturer="RYSE",
            model="SmartShade BLE",
            connections={(CONNECTION_BLUETOOTH, self._device.address)},
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to device updates when the entity is added."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self._device.register_position_callback(self._handle_position_update)
        )
        self.async_on_remove(
            self._device.register_disconnected_callback(self._handle_disconnect)
        )

    @callback
    def _handle_position_update(self, position: int) -> None:
        """Handle a position report pushed by the device."""
        if self._device.is_valid_position(position):
            real_position = self._device.get_real_position(position)
            self._current_position = real_position
            self._attr_is_closed = self._device.is_closed(position)
            _LOGGER.debug(
                "Updated cover position: raw=%d mapped=%d", position, real_position
            )
        self.async_write_ha_state()

    @callback
    def _handle_disconnect(self) -> None:
        """Handle the device dropping the connection."""
        self._attr_available = False
        self.async_write_ha_state()

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the shade."""
        try:
            await self._device.send_open()
        except (TimeoutError, OSError, BleakError) as err:
            raise HomeAssistantError(f"Failed to open cover: {err}") from err
        _LOGGER.debug("Change position to open")
        self._current_position = 100
        self._attr_is_closed = False
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the shade."""
        try:
            await self._device.send_close()
        except (TimeoutError, OSError, BleakError) as err:
            raise HomeAssistantError(f"Failed to close cover: {err}") from err
        _LOGGER.debug("Change position to close")
        self._current_position = 0
        self._attr_is_closed = True
        self.async_write_ha_state()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Set the shade to a specific position."""
        ha_position = kwargs[ATTR_POSITION]
        device_position = self._device.get_real_position(ha_position)
        try:
            await self._device.send_set_position(device_position)
        except (TimeoutError, OSError, BleakError) as err:
            raise HomeAssistantError(f"Failed to set cover position: {err}") from err
        _LOGGER.debug("Change position to a specific position")
        self._attr_is_closed = self._device.is_closed(device_position)
        self._current_position = ha_position
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Fetch the current state and position from the device."""
        try:
            if not self._device.is_connected and not await self._device.connect():
                if self._attr_available:
                    _LOGGER.debug("Failed to connect to device, skipping update")
                self._attr_available = False
                return

            self._attr_available = True

            if self._current_position is None:
                await self._device.send_get_position()

        except (TimeoutError, OSError, BleakError) as err:
            _LOGGER.warning(
                "BLE communication error while reading device data: %s", err
            )
            self._attr_available = False

    @property
    def current_cover_position(self) -> int | None:
        """Return current cover position."""
        if self._current_position is None:
            return None
        if not self._device.is_valid_position(self._current_position):
            _LOGGER.warning(
                "Invalid position value detected: %d",
                self._current_position,
            )
            return None
        return self._current_position
