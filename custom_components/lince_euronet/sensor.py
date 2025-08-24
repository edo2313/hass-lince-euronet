"""Sensor platform for Lince Euronet integration."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import LinceEuronetApi
from .const import DOMAIN, NUMERIC_SYSTEM_SENSORS
from .coordinator import LinceEuronetCoordinator

logger = logging.getLogger(__name__)


class LinceEuronetNumericSystemSensor(CoordinatorEntity, SensorEntity):
    """Numeric system sensor (battery, bus voltage, temperature, etc)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        unique_id: str,
        name: str,
        temp_idx: int,
        conversion_fn,
        unit,
        device_class,
    ) -> None:
        """Initialize numeric system sensor."""
        super().__init__(coordinator)
        self._unique_id = unique_id
        self._name = name
        self._temp_idx = temp_idx
        self._conversion_fn = conversion_fn
        self._attr_name = f"SistemaNum - {name}"
        self._attr_unique_id = f"system_number_{unique_id}_{coordinator.api.host}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.api.host)},
            name=f"Lince Euronet ({coordinator.api.host})",
            manufacturer="Lince",
        )
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_suggested_unit_of_measurement = unit

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        temp = self.coordinator.data["system_state"]
        if self._temp_idx < len(temp):
            raw = temp[self._temp_idx]
            self.native_value = self._conversion_fn(raw)
        self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Lince Euronet sensors from a config entry."""
    api: LinceEuronetApi = config_entry.runtime_data
    coordinator = LinceEuronetCoordinator(hass, config_entry, api)
    await coordinator.async_refresh()
    entities = []

    entities += [
        LinceEuronetNumericSystemSensor(coordinator, *args)
        for args in NUMERIC_SYSTEM_SENSORS
    ]

    async_add_entities(entities)
