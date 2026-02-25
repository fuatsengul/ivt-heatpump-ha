"""Sensor entities for IVT Heat Pump.

All temperatures, status values, energy data, and diagnostics.
Every sensor reads from coordinator.data — no direct API calls.
"""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfEnergy,
    UnitOfTemperature,
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    # HC
    HC_ROOM_TEMP,
    HC_CURRENT_SETPOINT,
    HC_TEMP_OVERRIDE,
    HC_STATUS,
    HC_COMFORT2_TEMP,
    HC_ECO_TEMP,
    HC_ACTIVE_PROGRAM,
    HC_HEAT_COOL_MODE,
    HC_SUWI_MODE,
    HC_SUWI_THRESHOLD,
    HC_HEATING_TYPE,
    HC_CONTROL_TYPE,
    HC_MAX_FLOW_TEMP,
    # DHW
    DHW_ACTUAL_TEMP,
    DHW_CURRENT_SETPOINT,
    DHW_STATUS,
    DHW_CHARGE,
    DHW_CHARGE_DURATION,
    DHW_SINGLE_CHARGE_SETPOINT,
    DHW_TEMP_ECO,
    DHW_TEMP_HIGH,
    DHW_TEMP_LOW,
    DHW_TD_MODE,
    # Heat Sources
    HS_ACTUAL_MODULATION,
    HS_SUPPLY_TEMP,
    HS_RETURN_TEMP,
    HS_CH_STATUS,
    HS_HEAT_DEMAND,
    HS_NUM_STARTS,
    HS_STANDBY,
    HS_EM_STATUS,
    HS_HS1_STARTS,
    # System
    SYS_OUTDOOR_TEMP,
    SYS_TYPE,
    # Gateway
    GW_FIRMWARE,
    GW_HARDWARE,
    GW_IP,
    GW_MAC,
    GW_SSID,
    GW_SERIAL,
    GW_SW_PREFIX,
    GW_TIMEZONE,
    # Notifications
    NOTIFICATIONS,
    # Energy recordings
    REC_TOTAL_COMPRESSOR,
    REC_TOTAL_EHEATER,
    REC_TOTAL_OUTPUT,
    REC_CH_COMPRESSOR,
    REC_CH_EHEATER,
    REC_CH_OUTPUT,
    REC_DHW_COMPRESSOR,
    REC_DHW_EHEATER,
    REC_DHW_OUTPUT,
)
from .coordinator import IVTDataCoordinator

_LOGGER = logging.getLogger(__name__)


# ── Sensor Definitions ───────────────────────────────────────
# (path, name, device_class, state_class, unit, icon, category)

TEMPERATURE_SENSORS = [
    (SYS_OUTDOOR_TEMP, "Outdoor Temperature", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:thermometer", None),
    (HC_ROOM_TEMP, "Room Temperature", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:home-thermometer", None),
    (HC_CURRENT_SETPOINT, "Heating Target", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:thermostat", None),
    (HC_TEMP_OVERRIDE, "Heating Override Setpoint", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:thermostat", "diagnostic"),
    (HC_COMFORT2_TEMP, "Heating Comfort Level", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:sofa", "diagnostic"),
    (HC_ECO_TEMP, "Heating ECO Level", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:leaf", "diagnostic"),
    (HC_MAX_FLOW_TEMP, "Max Flow Temperature", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:waves-arrow-up", "diagnostic"),
    (HS_SUPPLY_TEMP, "Supply Temperature", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:pipe", None),
    (HS_RETURN_TEMP, "Return Temperature", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:pipe", None),
    (DHW_ACTUAL_TEMP, "Hot Water Temperature", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:water-thermometer", None),
    (DHW_CURRENT_SETPOINT, "Hot Water Target", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:water-thermometer", None),
    (DHW_TEMP_ECO, "DHW ECO Level", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:leaf", "diagnostic"),
    (DHW_TEMP_LOW, "DHW ECO+ Level", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:leaf", "diagnostic"),
    (DHW_TEMP_HIGH, "DHW Comfort Level", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:fire", "diagnostic"),
    (DHW_SINGLE_CHARGE_SETPOINT, "Extra Hot Water Setpoint", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:water-boiler", "diagnostic"),
    (HC_SUWI_THRESHOLD, "Summer/Winter Threshold", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:sun-snowflake-variant", "diagnostic"),
]

STATUS_SENSORS = [
    (HC_STATUS, "Heating Status", None, None, None, "mdi:radiator", None),
    (HC_HEAT_COOL_MODE, "Heat/Cool Mode", None, None, None, "mdi:sun-snowflake-variant", "diagnostic"),
    (HC_SUWI_MODE, "Summer/Winter Mode", None, None, None, "mdi:sun-snowflake-variant", None),
    (HC_ACTIVE_PROGRAM, "Active Heating Program", None, None, None, "mdi:calendar-clock", "diagnostic"),
    (HC_HEATING_TYPE, "Heating Type", None, None, None, "mdi:radiator", "diagnostic"),
    (HC_CONTROL_TYPE, "Control Type", None, None, None, "mdi:tune", "diagnostic"),
    (DHW_STATUS, "Hot Water Status", None, None, None, "mdi:water-boiler", None),
    (DHW_CHARGE, "Extra Hot Water", None, None, None, "mdi:water-boiler-alert", None),
    (DHW_TD_MODE, "Thermal Disinfection", None, None, None, "mdi:shield-bug", "diagnostic"),
    (HS_CH_STATUS, "Central Heating Active", None, None, None, "mdi:fire", None),
    (HS_HEAT_DEMAND, "Heat Demand Source", None, None, None, "mdi:fire-circle", None),
    (HS_STANDBY, "Heat Pump Standby", None, None, None, "mdi:power-standby", "diagnostic"),
    (HS_EM_STATUS, "External Module Status", None, None, None, "mdi:expansion-card", "diagnostic"),
    (SYS_TYPE, "System Type", None, None, None, "mdi:heat-pump", "diagnostic"),
    (GW_SERIAL, "Gateway Serial", None, None, None, "mdi:identifier", "diagnostic"),
    (GW_FIRMWARE, "Gateway Firmware", None, None, None, "mdi:chip", "diagnostic"),
    (GW_HARDWARE, "Gateway Hardware", None, None, None, "mdi:chip", "diagnostic"),
    (GW_SW_PREFIX, "Gateway Software", None, None, None, "mdi:chip", "diagnostic"),
    (GW_IP, "Gateway IP Address", None, None, None, "mdi:ip-network", "diagnostic"),
    (GW_MAC, "Gateway MAC Address", None, None, None, "mdi:network-outline", "diagnostic"),
    (GW_SSID, "Gateway WiFi SSID", None, None, None, "mdi:wifi", "diagnostic"),
    (GW_TIMEZONE, "Gateway Timezone", None, None, None, "mdi:map-clock", "diagnostic"),
]

NUMERIC_SENSORS = [
    (HS_ACTUAL_MODULATION, "Compressor Modulation", None, SensorStateClass.MEASUREMENT, PERCENTAGE, "mdi:gauge", None),
    (HS_NUM_STARTS, "Heat Pump Starts", None, SensorStateClass.TOTAL_INCREASING, None, "mdi:counter", "diagnostic"),
    (DHW_CHARGE_DURATION, "Charge Duration Setting", None, None, "min", "mdi:timer-outline", "diagnostic"),
]

ENERGY_SENSORS = [
    (REC_TOTAL_COMPRESSOR, "Total Compressor Energy", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:lightning-bolt", None),
    (REC_TOTAL_EHEATER, "Total E-Heater Energy", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:lightning-bolt", None),
    (REC_TOTAL_OUTPUT, "Total Heat Output", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:fire-circle", None),
    (REC_CH_COMPRESSOR, "CH Compressor Energy", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:lightning-bolt", "diagnostic"),
    (REC_CH_EHEATER, "CH E-Heater Energy", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:lightning-bolt", "diagnostic"),
    (REC_CH_OUTPUT, "CH Heat Output", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:fire-circle", "diagnostic"),
    (REC_DHW_COMPRESSOR, "DHW Compressor Energy", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:lightning-bolt", "diagnostic"),
    (REC_DHW_EHEATER, "DHW E-Heater Energy", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:lightning-bolt", "diagnostic"),
    (REC_DHW_OUTPUT, "DHW Heat Output", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, UnitOfEnergy.KILO_WATT_HOUR, "mdi:fire-circle", "diagnostic"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities = []

    for path, name, dc, sc, unit, icon, cat in TEMPERATURE_SENSORS:
        entities.append(IVTSensor(coordinator, entry, path, name, dc, sc, unit, icon, cat))

    for path, name, dc, sc, unit, icon, cat in STATUS_SENSORS:
        entities.append(IVTSensor(coordinator, entry, path, name, dc, sc, unit, icon, cat))

    for path, name, dc, sc, unit, icon, cat in NUMERIC_SENSORS:
        entities.append(IVTSensor(coordinator, entry, path, name, dc, sc, unit, icon, cat))

    for path, name, dc, sc, unit, icon, cat in ENERGY_SENSORS:
        entities.append(IVTEnergySensor(coordinator, entry, path, name, dc, sc, unit, icon, cat))

    # Per-source compressor starts (from hs1/numberOfStarts values list)
    for key, label in [("ch", "CH"), ("dhw", "DHW"), ("cooling", "Cooling"), ("total", "Total")]:
        entities.append(
            IVTEmonSensor(
                coordinator, entry, HS_HS1_STARTS, key,
                f"{label} Compressor Starts",
                None, SensorStateClass.TOTAL_INCREASING, None,
                "mdi:counter", "diagnostic",
            )
        )

    # Notification count sensor
    entities.append(IVTNotificationSensor(coordinator, entry))

    async_add_entities(entities)


class IVTSensor(CoordinatorEntity, SensorEntity):
    """Generic sensor that reads a single API path from coordinator."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IVTDataCoordinator,
        entry: ConfigEntry,
        path: str,
        name: str,
        device_class,
        state_class,
        unit,
        icon: str,
        entity_category: str | None,
    ):
        super().__init__(coordinator)
        self._path = path
        self._attr_name = name
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        if entity_category:
            from homeassistant.helpers.entity import EntityCategory
            self._attr_entity_category = EntityCategory(entity_category)
        # Unique ID from path
        path_slug = path.replace("/", "_").strip("_")
        self._attr_unique_id = f"{entry.data['device_id']}_{path_slug}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data["device_id"])},
            "name": "IVT Heat Pump",
            "manufacturer": MANUFACTURER,
            "model": "K30",
        }

    @property
    def native_value(self):
        """Return sensor value."""
        val = self.coordinator.get_value(self._path)
        # Handle invalid float sentinel values
        if isinstance(val, (int, float)):
            if val in (32767.0, -32768.0):
                return None
        return val

    @property
    def available(self) -> bool:
        """Sensor is available if coordinator has data and value is not sentinel."""
        if not super().available:
            return False
        val = self.coordinator.get_value(self._path)
        if val is None:
            return False
        if isinstance(val, (int, float)) and val in (32767.0, -32768.0):
            return False
        return True


class IVTEnergySensor(IVTSensor):
    """Energy sensor that extracts cumulative kWh from recording data.

    Recording API returns data like:
    {
        "type": "recordedValue",
        "recordedResource": {"id": "/heatSources/emon/total/compressor"},
        "interval": ...,
        "recording": [{"c": 2.1, "d": "2024-01-01", "y": 123.4}, ...]
    }

    The cumulative value 'y' from the last recording entry gives total kWh.
    """

    @property
    def native_value(self):
        """Extract cumulative energy from recording data."""
        entry = self.coordinator.get_entry(self._path)
        if not entry:
            return None

        # Recording data format
        recording = entry.get("recording")
        if isinstance(recording, list) and len(recording) > 0:
            # Last entry's 'y' value = cumulative total
            last = recording[-1]
            if isinstance(last, dict):
                return last.get("y")

        # Fallback: maybe it's a simple value
        return entry.get("value")


class IVTEmonSensor(CoordinatorEntity, SensorEntity):
    """Sensor that reads a specific key from an emon-style values list.

    E.g. /heatSources/hs1/numberOfStarts has:
      values: [{"ch": 4052}, {"dhw": 519}, {"cooling": 0}, {"total": 4571}]
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IVTDataCoordinator,
        entry: ConfigEntry,
        path: str,
        key: str,
        name: str,
        device_class,
        state_class,
        unit,
        icon: str,
        entity_category: str | None,
    ):
        super().__init__(coordinator)
        self._path = path
        self._key = key
        self._attr_name = name
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        if entity_category:
            from homeassistant.helpers.entity import EntityCategory
            self._attr_entity_category = EntityCategory(entity_category)
        path_slug = path.replace("/", "_").strip("_")
        self._attr_unique_id = f"{entry.data['device_id']}_{path_slug}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data["device_id"])},
            "name": "IVT Heat Pump",
            "manufacturer": MANUFACTURER,
            "model": "K30",
        }

    @property
    def native_value(self):
        """Extract value for our key from the values list."""
        return self.coordinator.get_emon_value(self._path, self._key)


class IVTNotificationSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing number of active notifications/errors.

    /notifications returns: {"type": "errorList", "values": [...]}
    """

    _attr_has_entity_name = True
    _attr_name = "Active Notifications"
    _attr_icon = "mdi:bell-alert"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: IVTDataCoordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.data['device_id']}_notifications_count"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data["device_id"])},
            "name": "IVT Heat Pump",
            "manufacturer": MANUFACTURER,
            "model": "K30",
        }

    @property
    def native_value(self) -> int:
        """Number of active notifications."""
        values = self.coordinator.get_values_list(NOTIFICATIONS)
        if values is None:
            return 0
        return len(values)

    @property
    def extra_state_attributes(self) -> dict:
        """Include the notification details as attributes."""
        values = self.coordinator.get_values_list(NOTIFICATIONS)
        if values:
            return {"notifications": values}
        return {"notifications": []}
