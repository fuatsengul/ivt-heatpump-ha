"""Data update coordinator for IVT Heat Pump.

Polls the K30 API at a regular interval and stores all data centrally.
All entities read from coordinator.data instead of making their own API calls.
"""

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import IVTApi, IVTApiError, IVTAuthError
from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    # HC
    HC_ROOM_TEMP,
    HC_CURRENT_SETPOINT,
    HC_TEMP_OVERRIDE,
    HC_OPERATION_MODE,
    HC_ACTIVE_PROGRAM,
    HC_STATUS,
    HC_COMFORT2_TEMP,
    HC_ECO_TEMP,
    HC_MAX_FLOW_TEMP,
    HC_HEATING_TYPE,
    HC_CONTROL_TYPE,
    HC_HEAT_COOL_MODE,
    HC_SUWI_MODE,
    HC_SUWI_THRESHOLD,
    # DHW
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
    DHW_TD_MODE,
    DHW_REDUCE_TEMP_ON_ALARM,
    # Heat Sources
    HS_ACTUAL_MODULATION,
    HS_SUPPLY_TEMP,
    HS_RETURN_TEMP,
    HS_CH_STATUS,
    HS_HEAT_DEMAND,
    HS_NUM_STARTS,
    HS_STANDBY,
    HS_EM_STATUS,
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
    # Heat source per-source starts
    HS_HS1_STARTS,
    # Notifications
    NOTIFICATIONS,
    # Variable Tariff
    VT_CH_OPTIMIZATION,
    VT_CH_HIGH_DELTA,
    VT_CH_LOW_DELTA,
    VT_CH_MID_SETPOINT,
    VT_DHW_OPTIMIZATION,
    VT_DHW_HIGH_ENABLE,
    VT_DHW_LOW_ENABLE,
    # Recordings (energy)
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

_LOGGER = logging.getLogger(__name__)

# Paths polled every cycle (realtime data)
POLL_PATHS = [
    # Heating circuit
    HC_ROOM_TEMP,
    HC_CURRENT_SETPOINT,
    HC_TEMP_OVERRIDE,
    HC_OPERATION_MODE,
    HC_ACTIVE_PROGRAM,
    HC_STATUS,
    HC_COMFORT2_TEMP,
    HC_ECO_TEMP,
    HC_MAX_FLOW_TEMP,
    HC_HEAT_COOL_MODE,
    HC_SUWI_MODE,
    HC_SUWI_THRESHOLD,
    HC_HEATING_TYPE,
    HC_CONTROL_TYPE,
    # DHW
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
    DHW_TD_MODE,
    DHW_REDUCE_TEMP_ON_ALARM,
    # Heat sources
    HS_ACTUAL_MODULATION,
    HS_SUPPLY_TEMP,
    HS_RETURN_TEMP,
    HS_CH_STATUS,
    HS_HEAT_DEMAND,
    HS_NUM_STARTS,
    HS_STANDBY,
    HS_EM_STATUS,
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
    # Heat source per-source
    HS_HS1_STARTS,
    # Notifications
    NOTIFICATIONS,
    # Variable Tariff
    VT_CH_OPTIMIZATION,
    VT_CH_HIGH_DELTA,
    VT_CH_LOW_DELTA,
    VT_CH_MID_SETPOINT,
    VT_DHW_OPTIMIZATION,
    VT_DHW_HIGH_ENABLE,
    VT_DHW_LOW_ENABLE,
]

# Energy recording paths (polled less frequently)
ENERGY_PATHS = [
    REC_TOTAL_COMPRESSOR,
    REC_TOTAL_EHEATER,
    REC_TOTAL_OUTPUT,
    REC_CH_COMPRESSOR,
    REC_CH_EHEATER,
    REC_CH_OUTPUT,
    REC_DHW_COMPRESSOR,
    REC_DHW_EHEATER,
    REC_DHW_OUTPUT,
]


class IVTDataCoordinator(DataUpdateCoordinator):
    """Coordinator to poll IVT heat pump data."""

    def __init__(self, hass: HomeAssistant, api: IVTApi):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api
        self._energy_counter = 0  # Poll energy every 5th cycle

    async def _async_update_data(self) -> dict:
        """Fetch data from API.

        Returns:
            dict mapping API path → response dict (with 'value', 'unitOfMeasure', etc.)
        """
        try:
            data = await self.api.get_many(POLL_PATHS)

            # Poll energy data every 5 minutes (every 5th cycle at 60s interval)
            self._energy_counter += 1
            if self._energy_counter >= 5:
                self._energy_counter = 0
                energy_data = await self.api.get_many(ENERGY_PATHS)
                data.update(energy_data)
            elif self.data:
                # Carry forward previous energy data
                for path in ENERGY_PATHS:
                    if path in self.data:
                        data[path] = self.data[path]

            return data

        except IVTAuthError as err:
            raise UpdateFailed(f"Authentication error: {err}")
        except IVTApiError as err:
            raise UpdateFailed(f"API error: {err}")
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}")

    def get_value(self, path: str):
        """Get a value from the last poll. Returns None if unavailable."""
        if not self.data:
            return None
        entry = self.data.get(path)
        if entry and isinstance(entry, dict):
            return entry.get("value")
        return None

    def get_entry(self, path: str) -> dict | None:
        """Get the full response dict for a path."""
        if not self.data:
            return None
        return self.data.get(path)

    def get_values_list(self, path: str) -> list | None:
        """Get the 'values' list for endpoints like numberOfStarts, notifications.

        These endpoints return: {"id": "...", "values": [{...}, ...]}
        """
        entry = self.get_entry(path)
        if entry and isinstance(entry, dict):
            return entry.get("values")
        return None

    def get_emon_value(self, path: str, key: str) -> float | None:
        """Get a specific value from an emon-style values list.

        E.g. /heatSources/hs1/numberOfStarts has:
          values: [{"ch": 4052}, {"dhw": 519}, {"cooling": 0}, {"total": 4571}]
        """
        values = self.get_values_list(path)
        if values:
            for item in values:
                if isinstance(item, dict) and key in item:
                    return item[key]
        return None
