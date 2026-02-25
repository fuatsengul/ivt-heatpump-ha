"""Config flow for IVT Heat Pump integration."""

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IVTApi
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_DEVICE_ID,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_EXPIRES_AT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class IVTHeatPumpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle IVT Heat Pump config flow.

    Two setup options:
    1. Manual token entry (paste access_token + refresh_token + device_id)
    2. Full OAuth flow (login via browser → paste callback URL)
    """

    VERSION = 1

    def __init__(self):
        self._device_id = None
        self._auth_url = None

    async def async_step_user(self, user_input=None):
        """Handle user initiated flow — choose setup method."""
        if user_input is not None:
            method = user_input.get("method")
            if method == "oauth":
                return await self.async_step_oauth_start()
            else:
                return await self.async_step_manual()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("method", default="manual"): vol.In({
                    "manual": "Manual (paste tokens from tokens.json)",
                    "oauth": "OAuth Login (browser login flow)",
                }),
            }),
        )

    # ── Manual Token Entry ───────────────────────────────────

    async def async_step_manual(self, user_input=None):
        """Manual entry of device_id, access_token, refresh_token."""
        errors = {}

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID].strip()
            access_token = user_input[CONF_ACCESS_TOKEN].strip()
            refresh_token = user_input.get(CONF_REFRESH_TOKEN, "").strip()
            expires_at = user_input.get(CONF_TOKEN_EXPIRES_AT, "").strip()

            # Test connection
            session = async_get_clientsession(self.hass)
            api = IVTApi(
                session=session,
                device_id=device_id,
                access_token=access_token,
                refresh_token=refresh_token or None,
            )

            if await api.test_connection():
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"IVT Heat Pump ({device_id})",
                    data={
                        CONF_DEVICE_ID: device_id,
                        CONF_ACCESS_TOKEN: access_token,
                        CONF_REFRESH_TOKEN: refresh_token or None,
                        CONF_TOKEN_EXPIRES_AT: expires_at or None,
                    },
                )
            else:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICE_ID): str,
                vol.Required(CONF_ACCESS_TOKEN): str,
                vol.Optional(CONF_REFRESH_TOKEN): str,
                vol.Optional(CONF_TOKEN_EXPIRES_AT): str,
            }),
            errors=errors,
            description_placeholders={
                "tip": "Get these values from your tokens.json file"
            },
        )

    # ── OAuth Flow ───────────────────────────────────────────

    async def async_step_oauth_start(self, user_input=None):
        """Step 1: Show the OAuth URL and ask for device_id."""
        errors = {}

        if user_input is not None:
            self._device_id = user_input[CONF_DEVICE_ID].strip()
            self._auth_url = IVTApi.build_auth_url()
            return await self.async_step_oauth_callback()

        return self.async_show_form(
            step_id="oauth_start",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICE_ID): str,
            }),
            errors=errors,
            description_placeholders={
                "info": "Enter your device ID (from the IVT app or serial number)"
            },
        )

    async def async_step_oauth_callback(self, user_input=None):
        """Step 2: User logs in and pastes the callback URL."""
        errors = {}

        if user_input is not None:
            callback_url = user_input.get("callback_url", "").strip()
            code = IVTApi.extract_code_from_url(callback_url)

            if not code:
                errors["base"] = "invalid_code"
            else:
                session = async_get_clientsession(self.hass)
                api = IVTApi(
                    session=session,
                    device_id=self._device_id,
                    access_token="pending",
                )

                tokens = await api.exchange_code_for_tokens(code)
                if tokens:
                    await self.async_set_unique_id(self._device_id)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=f"IVT Heat Pump ({self._device_id})",
                        data={
                            CONF_DEVICE_ID: self._device_id,
                            CONF_ACCESS_TOKEN: tokens["access_token"],
                            CONF_REFRESH_TOKEN: tokens["refresh_token"],
                            CONF_TOKEN_EXPIRES_AT: tokens["expires_at"],
                        },
                    )
                else:
                    errors["base"] = "token_exchange_failed"

        return self.async_show_form(
            step_id="oauth_callback",
            data_schema=vol.Schema({
                vol.Required("callback_url"): str,
            }),
            errors=errors,
            description_placeholders={
                "auth_url": self._auth_url or IVTApi.build_auth_url(),
                "info": "Open the URL above in a browser, log in, then paste the callback URL here",
            },
        )
