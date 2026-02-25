"""Binary sensor entities for IVT Heat Pump — problem/alert indicators."""

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, NOTIFICATIONS
from .coordinator import IVTDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    async_add_entities([IVTNotificationBinarySensor(coordinator, entry)])


class IVTNotificationBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor that is ON when there are active notifications/errors."""

    _attr_has_entity_name = True
    _attr_name = "Problem"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:alert-circle"

    def __init__(self, coordinator: IVTDataCoordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.data['device_id']}_problem"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data["device_id"])},
            "name": "IVT Heat Pump",
            "manufacturer": MANUFACTURER,
            "model": "K30",
        }

    @property
    def is_on(self) -> bool:
        """True when there are active notifications."""
        values = self.coordinator.get_values_list(NOTIFICATIONS)
        return bool(values and len(values) > 0)

    @property
    def extra_state_attributes(self) -> dict:
        """Notification details."""
        values = self.coordinator.get_values_list(NOTIFICATIONS)
        return {
            "notification_count": len(values) if values else 0,
            "notifications": values or [],
        }
