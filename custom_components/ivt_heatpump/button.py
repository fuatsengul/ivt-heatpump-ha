"""Button entities for IVT Heat Pump — one-shot actions."""

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, DHW_CHARGE
from .coordinator import IVTDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    async_add_entities([
        IVTChargeButton(coordinator, entry, "start"),
        IVTChargeButton(coordinator, entry, "stop"),
    ])


class IVTChargeButton(CoordinatorEntity, ButtonEntity):
    """Button to start/stop Extra Hot Water charge."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IVTDataCoordinator,
        entry: ConfigEntry,
        action: str,
    ):
        super().__init__(coordinator)
        self._action = action
        if action == "start":
            self._attr_name = "Start Extra Hot Water"
            self._attr_icon = "mdi:water-boiler"
        else:
            self._attr_name = "Stop Extra Hot Water"
            self._attr_icon = "mdi:water-boiler-off"
        self._attr_unique_id = f"{entry.data['device_id']}_btn_charge_{action}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data["device_id"])},
            "name": "IVT Heat Pump",
            "manufacturer": MANUFACTURER,
            "model": "K30",
        }

    async def async_press(self) -> None:
        """Handle button press."""
        await self.coordinator.api.put(DHW_CHARGE, self._action)
        await self.coordinator.async_request_refresh()
