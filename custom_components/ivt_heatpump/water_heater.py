"""Water heater entity for IVT Heat Pump hot water (DHW).

K30 DHW API:
  Modes: Off / low (ECO+) / eco (ECO) / high (Comfort) / ownprogram (Auto)
  Each mode has its own temperature level via temperatureLevels/
  Extra Hot Water: charge start/stop → heats to singleChargeSetpoint
"""

import logging

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    DHW_ACTUAL_TEMP,
    DHW_CURRENT_SETPOINT,
    DHW_OPERATION_MODE,
    DHW_STATUS,
    DHW_CHARGE,
    DHW_CHARGE_DURATION,
    DHW_SINGLE_CHARGE_SETPOINT,
    DHW_TEMP_ECO,
    DHW_TEMP_HIGH,
    DHW_TEMP_LOW,
    DHW_TEMP_OFF,
    DHW_MODE_OFF,
    DHW_MODE_LOW,
    DHW_MODE_ECO,
    DHW_MODE_HIGH,
    DHW_MODE_AUTO,
    DHW_TEMP_LIMITS,
)
from .coordinator import IVTDataCoordinator

_LOGGER = logging.getLogger(__name__)

# HA operation mode names (user-friendly)
HA_MODE_OFF = "off"
HA_MODE_ECO_PLUS = "eco+"       # low
HA_MODE_ECO = "eco"             # eco
HA_MODE_COMFORT = "performance" # high
HA_MODE_AUTO = "auto"           # ownprogram

# Mapping: HA name → Bosch API value
HA_TO_BOSCH = {
    HA_MODE_OFF: DHW_MODE_OFF,
    HA_MODE_ECO_PLUS: DHW_MODE_LOW,
    HA_MODE_ECO: DHW_MODE_ECO,
    HA_MODE_COMFORT: DHW_MODE_HIGH,
    HA_MODE_AUTO: DHW_MODE_AUTO,
}
BOSCH_TO_HA = {v: k for k, v in HA_TO_BOSCH.items()}

# Bosch mode → temperature level path
MODE_TO_TEMP_PATH = {
    DHW_MODE_ECO: DHW_TEMP_ECO,
    DHW_MODE_LOW: DHW_TEMP_LOW,
    DHW_MODE_HIGH: DHW_TEMP_HIGH,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up water heater entity."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    async_add_entities([IVTWaterHeater(coordinator, entry)])


class IVTWaterHeater(CoordinatorEntity, WaterHeaterEntity):
    """Water heater entity for IVT DHW circuit."""

    _attr_has_entity_name = True
    _attr_name = "Hot Water"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_operation_list = [
        HA_MODE_OFF,
        HA_MODE_ECO_PLUS,
        HA_MODE_ECO,
        HA_MODE_COMFORT,
        HA_MODE_AUTO,
    ]
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
        | WaterHeaterEntityFeature.AWAY_MODE
    )

    def __init__(self, coordinator: IVTDataCoordinator, entry: ConfigEntry):
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.data['device_id']}_water_heater_dhw1"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data["device_id"])},
            "name": "IVT Heat Pump",
            "manufacturer": MANUFACTURER,
            "model": "K30",
        }

    # ── State Properties ─────────────────────────────────────

    @property
    def current_temperature(self) -> float | None:
        """Current water temperature."""
        return self.coordinator.get_value(DHW_ACTUAL_TEMP)

    @property
    def target_temperature(self) -> float | None:
        """Target temperature for current mode.

        Each mode has its own target from temperatureLevels/.
        In auto mode, we show currentSetpoint.
        """
        bosch_mode = self.coordinator.get_value(DHW_OPERATION_MODE)
        if bosch_mode in MODE_TO_TEMP_PATH:
            return self.coordinator.get_value(MODE_TO_TEMP_PATH[bosch_mode])
        # For auto/off, show the currentSetpoint (read-only)
        return self.coordinator.get_value(DHW_CURRENT_SETPOINT)

    @property
    def min_temp(self) -> float:
        """Min temperature for current mode."""
        bosch_mode = self.coordinator.get_value(DHW_OPERATION_MODE)
        limits = DHW_TEMP_LIMITS.get(bosch_mode)
        return limits["min"] if limits else 30.0

    @property
    def max_temp(self) -> float:
        """Max temperature for current mode."""
        bosch_mode = self.coordinator.get_value(DHW_OPERATION_MODE)
        limits = DHW_TEMP_LIMITS.get(bosch_mode)
        return limits["max"] if limits else 70.0

    @property
    def current_operation(self) -> str | None:
        """Current operation mode (HA name)."""
        bosch_mode = self.coordinator.get_value(DHW_OPERATION_MODE)
        return BOSCH_TO_HA.get(bosch_mode, bosch_mode)

    @property
    def is_away_mode_on(self) -> bool:
        """Away mode = Extra Hot Water (charge active)."""
        return self.coordinator.get_value(DHW_CHARGE) == "start"

    @property
    def extra_state_attributes(self) -> dict:
        """Extra attributes."""
        return {
            "operation_mode_raw": self.coordinator.get_value(DHW_OPERATION_MODE),
            "current_setpoint": self.coordinator.get_value(DHW_CURRENT_SETPOINT),
            "charge_active": self.coordinator.get_value(DHW_CHARGE) == "start",
            "charge_duration_mins": self.coordinator.get_value(DHW_CHARGE_DURATION),
            "charge_setpoint": self.coordinator.get_value(DHW_SINGLE_CHARGE_SETPOINT),
            "status": self.coordinator.get_value(DHW_STATUS),
            "eco_temp": self.coordinator.get_value(DHW_TEMP_ECO),
            "eco_plus_temp": self.coordinator.get_value(DHW_TEMP_LOW),
            "comfort_temp": self.coordinator.get_value(DHW_TEMP_HIGH),
        }

    # ── Commands ─────────────────────────────────────────────

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set DHW operation mode."""
        bosch_mode = HA_TO_BOSCH.get(operation_mode)
        if bosch_mode:
            await self.coordinator.api.put(DHW_OPERATION_MODE, bosch_mode)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.warning("Unknown DHW mode: %s", operation_mode)

    async def async_set_temperature(self, **kwargs) -> None:
        """Set target temperature for the current mode.

        Writes to the temperatureLevels/ endpoint for the active mode.
        """
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return

        bosch_mode = self.coordinator.get_value(DHW_OPERATION_MODE)
        temp_path = MODE_TO_TEMP_PATH.get(bosch_mode)

        if temp_path:
            await self.coordinator.api.put(temp_path, temp)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.warning(
                "Cannot set temperature in mode %s (no writeable setpoint)",
                bosch_mode,
            )

    async def async_turn_away_mode_on(self) -> None:
        """Start Extra Hot Water charge."""
        await self.coordinator.api.put(DHW_CHARGE, "start")
        await self.coordinator.async_request_refresh()

    async def async_turn_away_mode_off(self) -> None:
        """Stop Extra Hot Water charge."""
        await self.coordinator.api.put(DHW_CHARGE, "stop")
        await self.coordinator.async_request_refresh()
