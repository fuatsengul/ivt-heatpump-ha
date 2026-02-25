"""Switch entities for IVT Heat Pump — on/off toggleable settings."""

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    DHW_REDUCE_TEMP_ON_ALARM,
    VT_CH_OPTIMIZATION,
    VT_DHW_OPTIMIZATION,
    VT_DHW_HIGH_ENABLE,
    VT_DHW_LOW_ENABLE,
)
from .coordinator import IVTDataCoordinator

_LOGGER = logging.getLogger(__name__)

# (path, name, on_value, off_value, icon, category)
SWITCH_ENTITIES = [
    (DHW_REDUCE_TEMP_ON_ALARM, "Reduce DHW Temp on Alarm", "on", "off", "mdi:alert-outline", "config"),
    (VT_CH_OPTIMIZATION, "Tariff CH Optimization", "on", "off", "mdi:cash-fast", "config"),
    (VT_DHW_OPTIMIZATION, "Tariff DHW Optimization", "on", "off", "mdi:cash-fast", "config"),
    (VT_DHW_HIGH_ENABLE, "Tariff DHW High Price", "yes", "no", "mdi:cash-plus", "config"),
    (VT_DHW_LOW_ENABLE, "Tariff DHW Low Price", "yes", "no", "mdi:cash-minus", "config"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities = []
    for path, name, on_val, off_val, icon, cat in SWITCH_ENTITIES:
        entities.append(IVTSwitch(coordinator, entry, path, name, on_val, off_val, icon, cat))

    async_add_entities(entities)


class IVTSwitch(CoordinatorEntity, SwitchEntity):
    """Toggle switch backed by a K30 string value (on/off or yes/no)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IVTDataCoordinator,
        entry: ConfigEntry,
        path: str,
        name: str,
        on_value: str,
        off_value: str,
        icon: str,
        entity_category: str | None,
    ):
        super().__init__(coordinator)
        self._path = path
        self._on_value = on_value
        self._off_value = off_value
        self._attr_name = name
        self._attr_icon = icon
        if entity_category:
            self._attr_entity_category = EntityCategory(entity_category)
        path_slug = path.replace("/", "_").strip("_")
        self._attr_unique_id = f"{entry.data['device_id']}_sw_{path_slug}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data["device_id"])},
            "name": "IVT Heat Pump",
            "manufacturer": MANUFACTURER,
            "model": "K30",
        }

    @property
    def is_on(self) -> bool | None:
        """Current state."""
        val = self.coordinator.get_value(self._path)
        if val is None:
            return None
        return val == self._on_value

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on."""
        await self.coordinator.api.put(self._path, self._on_value)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off."""
        await self.coordinator.api.put(self._path, self._off_value)
        await self.coordinator.async_request_refresh()
