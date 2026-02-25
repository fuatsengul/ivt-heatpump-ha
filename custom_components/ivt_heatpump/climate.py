"""Climate entity for IVT Heat Pump heating circuit.

Maps directly to the K30 API:
  - Modes: manual (heat) / auto (auto)
  - Temperature: temporaryRoomSetpoint (5–30°C)
  - Schedule levels: comfort2 / eco
  - Programs: A / B
"""

import logging

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    HC_ROOM_TEMP,
    HC_CURRENT_SETPOINT,
    HC_TEMP_OVERRIDE,
    HC_OPERATION_MODE,
    HC_ACTIVE_PROGRAM,
    HC_STATUS,
    HC_COMFORT2_TEMP,
    HC_ECO_TEMP,
    HC_HEAT_COOL_MODE,
    HC_SUWI_MODE,
    HC_TEMP_MIN,
    HC_TEMP_MAX,
    HC_MODE_MANUAL,
    HC_MODE_AUTO,
)
from .coordinator import IVTDataCoordinator

_LOGGER = logging.getLogger(__name__)

# Preset modes correspond to schedule temperature levels
PRESET_COMFORT = "comfort"
PRESET_ECO = "eco"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up climate entity."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    async_add_entities([IVTClimate(coordinator, entry)])


class IVTClimate(CoordinatorEntity, ClimateEntity):
    """Climate entity for IVT heating circuit (hc1)."""

    _attr_has_entity_name = True
    _attr_name = "Heating"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = HC_TEMP_MIN
    _attr_max_temp = HC_TEMP_MAX
    _attr_target_temperature_step = 0.5
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.AUTO]
    _attr_preset_modes = [PRESET_COMFORT, PRESET_ECO]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
    )

    def __init__(self, coordinator: IVTDataCoordinator, entry: ConfigEntry):
        """Initialize."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.data['device_id']}_climate_hc1"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data["device_id"])},
            "name": "IVT Heat Pump",
            "manufacturer": MANUFACTURER,
            "model": "K30",
        }

    # ── State Properties ─────────────────────────────────────

    @property
    def current_temperature(self) -> float | None:
        """Current room temperature."""
        return self.coordinator.get_value(HC_ROOM_TEMP)

    @property
    def target_temperature(self) -> float | None:
        """Target temperature.

        In manual mode: temporaryRoomSetpoint (user-set override)
        In auto mode: currentRoomSetpoint (schedule-determined)
        """
        mode = self.coordinator.get_value(HC_OPERATION_MODE)
        if mode == HC_MODE_MANUAL:
            return self.coordinator.get_value(HC_TEMP_OVERRIDE)
        return self.coordinator.get_value(HC_CURRENT_SETPOINT)

    @property
    def hvac_mode(self) -> HVACMode:
        """Current HVAC mode."""
        mode = self.coordinator.get_value(HC_OPERATION_MODE)
        if mode == HC_MODE_AUTO:
            return HVACMode.AUTO
        return HVACMode.HEAT  # manual

    @property
    def hvac_action(self) -> HVACAction | None:
        """Current HVAC action based on status and heat demand."""
        status = self.coordinator.get_value(HC_STATUS)
        if status == "ch_disabled":
            return HVACAction.OFF

        heat_cool = self.coordinator.get_value(HC_HEAT_COOL_MODE)
        suwi = self.coordinator.get_value(HC_SUWI_MODE)

        if suwi == "cooling":
            return HVACAction.COOLING

        # Check if actively heating by comparing temps
        current = self.current_temperature
        target = self.target_temperature
        if current is not None and target is not None:
            if current < target - 0.3:
                return HVACAction.HEATING
            return HVACAction.IDLE

        return HVACAction.IDLE

    @property
    def preset_mode(self) -> str | None:
        """Current preset based on active schedule level.

        In auto mode, the schedule alternates between comfort2 and eco.
        We show which level is currently active based on target temp.
        """
        current_setpoint = self.coordinator.get_value(HC_CURRENT_SETPOINT)
        comfort2 = self.coordinator.get_value(HC_COMFORT2_TEMP)
        eco = self.coordinator.get_value(HC_ECO_TEMP)

        if current_setpoint is not None and comfort2 is not None:
            if abs(current_setpoint - comfort2) < 0.3:
                return PRESET_COMFORT
        if current_setpoint is not None and eco is not None:
            if abs(current_setpoint - eco) < 0.3:
                return PRESET_ECO
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Extra attributes for diagnostics."""
        return {
            "operation_mode_raw": self.coordinator.get_value(HC_OPERATION_MODE),
            "active_program": self.coordinator.get_value(HC_ACTIVE_PROGRAM),
            "comfort2_temp": self.coordinator.get_value(HC_COMFORT2_TEMP),
            "eco_temp": self.coordinator.get_value(HC_ECO_TEMP),
            "temporary_setpoint": self.coordinator.get_value(HC_TEMP_OVERRIDE),
            "current_setpoint": self.coordinator.get_value(HC_CURRENT_SETPOINT),
            "heat_cool_mode": self.coordinator.get_value(HC_HEAT_COOL_MODE),
            "summer_winter_mode": self.coordinator.get_value(HC_SUWI_MODE),
            "status": self.coordinator.get_value(HC_STATUS),
        }

    # ── Commands ─────────────────────────────────────────────

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode (manual/auto)."""
        if hvac_mode == HVACMode.AUTO:
            await self.coordinator.api.put(HC_OPERATION_MODE, HC_MODE_AUTO)
        elif hvac_mode == HVACMode.HEAT:
            await self.coordinator.api.put(HC_OPERATION_MODE, HC_MODE_MANUAL)
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs) -> None:
        """Set target temperature.

        Always writes to temporaryRoomSetpoint (5–30°C).
        In auto mode this creates a temporary override.
        In manual mode this is the permanent setpoint.
        """
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is not None:
            await self.coordinator.api.put(HC_TEMP_OVERRIDE, temp)
            await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set preset mode.

        In auto mode, this sets the temperature override to the comfort2 or eco level.
        """
        if preset_mode == PRESET_COMFORT:
            temp = self.coordinator.get_value(HC_COMFORT2_TEMP)
        elif preset_mode == PRESET_ECO:
            temp = self.coordinator.get_value(HC_ECO_TEMP)
        else:
            return

        if temp is not None:
            await self.coordinator.api.put(HC_TEMP_OVERRIDE, temp)
            await self.coordinator.async_request_refresh()
