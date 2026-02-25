"""IVT Heat Pump integration for Home Assistant."""

import logging
from datetime import datetime, timezone

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IVTApi
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_DEVICE_ID,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_EXPIRES_AT,
    DOMAIN,
    GW_FIRMWARE,
    GW_HARDWARE,
    GW_SERIAL,
    GW_MAC,
    SYS_TYPE,
)
from .coordinator import IVTDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["climate", "water_heater", "sensor", "binary_sensor", "number", "switch", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up IVT Heat Pump from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)

    # Parse token expiry
    expires_at = entry.data.get(CONF_TOKEN_EXPIRES_AT)
    if expires_at and isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)

    async def _on_token_refresh(access_token, refresh_token, token_expires_at):
        """Persist refreshed tokens in HA config entry."""
        new_data = {**entry.data}
        new_data[CONF_ACCESS_TOKEN] = access_token
        new_data[CONF_REFRESH_TOKEN] = refresh_token
        new_data[CONF_TOKEN_EXPIRES_AT] = token_expires_at.isoformat()
        hass.config_entries.async_update_entry(entry, data=new_data)
        _LOGGER.debug("Persisted refreshed tokens to config entry")

    api = IVTApi(
        session=session,
        device_id=entry.data[CONF_DEVICE_ID],
        access_token=entry.data[CONF_ACCESS_TOKEN],
        refresh_token=entry.data.get(CONF_REFRESH_TOKEN),
        token_expires_at=expires_at,
        on_token_refresh=_on_token_refresh,
    )

    coordinator = IVTDataCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    # Enrich device info from first poll data
    device_id = entry.data[CONF_DEVICE_ID]
    fw_version = coordinator.get_value(GW_FIRMWARE)
    hw_version = coordinator.get_value(GW_HARDWARE)
    serial = coordinator.get_value(GW_SERIAL)
    mac_addr = coordinator.get_value(GW_MAC)
    sys_type = coordinator.get_value(SYS_TYPE)
    model = f"K30 ({sys_type})" if sys_type and sys_type != "unknown" else "K30"

    # Register device with enriched info
    from homeassistant.helpers import device_registry as dr
    dev_reg = dr.async_get(hass)
    dev_reg.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, device_id)},
        name="IVT Heat Pump",
        manufacturer="Bosch / IVT",
        model=model,
        sw_version=fw_version,
        hw_version=hw_version,
        serial_number=serial or device_id,
        connections={(dr.CONNECTION_NETWORK_MAC, mac_addr)} if mac_addr else set(),
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
