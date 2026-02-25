"""Number entities for IVT Heat Pump — writeable numeric settings.

These are settings you can adjust directly, exposed as number sliders in HA.
"""

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    HC_COMFORT2_TEMP,
    HC_ECO_TEMP,
    HC_MAX_FLOW_TEMP,
    HC_SUWI_THRESHOLD,
    DHW_TEMP_ECO,
    DHW_TEMP_HIGH,
    DHW_TEMP_LOW,
    DHW_SINGLE_CHARGE_SETPOINT,
    DHW_CHARGE_DURATION,
    VT_CH_HIGH_DELTA,
    VT_CH_LOW_DELTA,
    VT_CH_MID_SETPOINT,
)
from .coordinator import IVTDataCoordinator

_LOGGER = logging.getLogger(__name__)

# (path, name, min, max, step, unit, icon, mode, category)
NUMBER_ENTITIES = [
    # Heating levels
    (HC_COMFORT2_TEMP, "Heating Comfort Level", 20.5, 30.0, 0.5, UnitOfTemperature.CELSIUS, "mdi:sofa", NumberMode.SLIDER, None),
    (HC_ECO_TEMP, "Heating ECO Level", 5.0, 20.5, 0.5, UnitOfTemperature.CELSIUS, "mdi:leaf", NumberMode.SLIDER, None),
    (HC_MAX_FLOW_TEMP, "Max Flow Temperature", 30.0, 85.0, 1.0, UnitOfTemperature.CELSIUS, "mdi:waves-arrow-up", NumberMode.SLIDER, "config"),
    (HC_SUWI_THRESHOLD, "Summer/Winter Threshold", 10.0, 30.0, 0.5, UnitOfTemperature.CELSIUS, "mdi:sun-snowflake-variant", NumberMode.SLIDER, "config"),
    # DHW levels
    (DHW_TEMP_ECO, "DHW ECO Temperature", 30.0, 43.0, 0.5, UnitOfTemperature.CELSIUS, "mdi:leaf", NumberMode.SLIDER, None),
    (DHW_TEMP_LOW, "DHW ECO+ Temperature", 30.0, 48.0, 0.5, UnitOfTemperature.CELSIUS, "mdi:leaf", NumberMode.SLIDER, None),
    (DHW_TEMP_HIGH, "DHW Comfort Temperature", 30.0, 47.0, 0.5, UnitOfTemperature.CELSIUS, "mdi:fire", NumberMode.SLIDER, None),
    (DHW_SINGLE_CHARGE_SETPOINT, "Extra Hot Water Setpoint", 50.0, 70.0, 1.0, UnitOfTemperature.CELSIUS, "mdi:water-boiler", NumberMode.SLIDER, "config"),
    (DHW_CHARGE_DURATION, "Charge Duration", 15.0, 2880.0, 15.0, "min", "mdi:timer-outline", NumberMode.BOX, "config"),
    # Variable tariff
    (VT_CH_HIGH_DELTA, "Tariff High Price Delta", 0.5, 2.0, 0.5, None, "mdi:cash-plus", NumberMode.SLIDER, "config"),
    (VT_CH_LOW_DELTA, "Tariff Low Price Delta", 0.0, 2.0, 0.5, None, "mdi:cash-minus", NumberMode.SLIDER, "config"),
    (VT_CH_MID_SETPOINT, "Tariff Mid Price Setpoint", 7.0, 28.0, 0.5, UnitOfTemperature.CELSIUS, "mdi:cash", NumberMode.SLIDER, "config"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities = []
    for path, name, mn, mx, step, unit, icon, mode, cat in NUMBER_ENTITIES:
        entities.append(
            IVTNumber(coordinator, entry, path, name, mn, mx, step, unit, icon, mode, cat)
        )

    async_add_entities(entities)


class IVTNumber(CoordinatorEntity, NumberEntity):
    """Writeable number entity backed by a K30 API endpoint."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IVTDataCoordinator,
        entry: ConfigEntry,
        path: str,
        name: str,
        native_min: float,
        native_max: float,
        native_step: float,
        unit,
        icon: str,
        mode: NumberMode,
        entity_category: str | None,
    ):
        super().__init__(coordinator)
        self._path = path
        self._attr_name = name
        self._attr_native_min_value = native_min
        self._attr_native_max_value = native_max
        self._attr_native_step = native_step
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_mode = mode
        if entity_category:
            self._attr_entity_category = EntityCategory(entity_category)
        path_slug = path.replace("/", "_").strip("_")
        self._attr_unique_id = f"{entry.data['device_id']}_num_{path_slug}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data["device_id"])},
            "name": "IVT Heat Pump",
            "manufacturer": MANUFACTURER,
            "model": "K30",
        }

    @property
    def native_value(self) -> float | None:
        """Current value."""
        return self.coordinator.get_value(self._path)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value via API."""
        await self.coordinator.api.put(self._path, value)
        await self.coordinator.async_request_refresh()
