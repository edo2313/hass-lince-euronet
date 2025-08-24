"""Binary sensor platform for Lince Euronet integration."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import LinceEuronetApi
from .const import (
    DOMAIN,
    GSTATE_SYSTEM_SENSORS,
    INGRESSI_COLUMNS,
    SYSTEM_STATUS_SENSORS,
)
from .coordinator import LinceEuronetCoordinator

logger = logging.getLogger(__name__)


class LinceEuronetGStateSensor(CoordinatorEntity, BinarySensorEntity):
    """Sensor for gstate system status (G1, G2, G3, Gext, Servizio)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LinceEuronetCoordinator,
        unique_id: str,
        name: str,
        char: str,
    ) -> None:
        """Initialize gstate system sensor."""
        super().__init__(coordinator)
        self._unique_id = unique_id
        self._name = name
        self._char = char
        self._attr_name = f"Programma - {name}"
        self._attr_unique_id = f"system_gstate_{unique_id}_{coordinator.api.host}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.api.host)},
            name=f"Lince Euronet ({coordinator.api.host})",
            manufacturer="Lince",
        )
        self._attr_device_class = BinarySensorDeviceClass.RUNNING

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self._char in self.coordinator.data["g_state"]
        self.async_write_ha_state()


class LinceEuronetSystemSensor(CoordinatorEntity, BinarySensorEntity):
    """Sensor for system status bitmask values."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator, unique_id: str, name: str, temp_idx: int, bitmask: int
    ) -> None:
        """Initialize system status bitmask sensor."""
        super().__init__(coordinator)
        self._unique_id = unique_id
        self._name = name
        self._temp_idx = temp_idx
        self._bitmask = bitmask
        self._unavailable_logged = False
        self._attr_name = f"Sistema - {name}"
        self._attr_unique_id = f"system_state_{unique_id}_{coordinator.api.host}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.api.host)},
            name=f"Lince Euronet ({coordinator.api.host})",
            manufacturer="Lince",
        )
        self._attr_device_class = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = (
            self.coordinator.data["system_state"][self._temp_idx] & self._bitmask != 0
        )
        self.async_write_ha_state()


class LinceEuronetIngressoSensor(CoordinatorEntity, BinarySensorEntity):
    """Sensor for a single ingresso input state."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, ingresso: str, key: str, index: int) -> None:
        """Initialize ingresso sensor."""
        super().__init__(coordinator)
        self._ingresso = ingresso
        self._key = key
        self._index = index
        self._unavailable_logged = False
        self._attr_name = f"Ingresso - {ingresso} {key.replace('_', ' ').title() if key != 'ingresso_aperto' else ''}"
        self._attr_unique_id = f"{ingresso.replace(' ', '_').lower()}_{key}_{index}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.api.host)},
            name=f"Lince Euronet ({coordinator.api.host})",
            manufacturer="Lince",
        )
        self._attr_device_class = BinarySensorDeviceClass.OPENING
        # Disable by default for specific keys
        if key in ("allarme_24h", "ingresso_escluso", "memoria_24h", "memoria_allarme"):
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
            self._attr_entity_registry_enabled_default = False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        col_idx = INGRESSI_COLUMNS.index(self._key)
        self._attr_is_on = (
            self.coordinator.data["ingressi_state"][col_idx] >> self._index
        ) & 1
        self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Lince Euronet sensors from a config entry."""
    api: LinceEuronetApi = config_entry.runtime_data
    coordinator = LinceEuronetCoordinator(hass, config_entry, api)
    ingressi = await api.async_get_ingressi_config()  # Get sensor names from HTML once

    await coordinator.async_refresh()

    entities = []
    entities += [
        LinceEuronetGStateSensor(coordinator, *args) for args in GSTATE_SYSTEM_SENSORS
    ]
    entities += [
        LinceEuronetSystemSensor(coordinator, *args) for args in SYSTEM_STATUS_SENSORS
    ]
    entities += [
        LinceEuronetIngressoSensor(coordinator, ingresso, key, idx)
        for idx, ingresso in enumerate(ingressi)
        for key in INGRESSI_COLUMNS
    ]
    async_add_entities(entities)
