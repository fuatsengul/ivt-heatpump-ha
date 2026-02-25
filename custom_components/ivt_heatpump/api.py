"""API client for IVT Heat Pump via Bosch PoinTT OAuth2 API.

This is a clean, standalone client — no database JSON, no generic abstractions.
Direct HTTP calls to the K30 API endpoints.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone

import aiohttp

from .const import (
    CLIENT_ID,
    CODE_VERIFIER,
    POINTT_BASE_URL,
    REDIRECT_URI,
    SCOPES,
    TOKEN_URL,
)

_LOGGER = logging.getLogger(__name__)


class IVTApiError(Exception):
    """Base exception for API errors."""


class IVTAuthError(IVTApiError):
    """Authentication/token error."""


class IVTConnectionError(IVTApiError):
    """Connection error."""


class IVTApi:
    """Direct API client for IVT K30 heat pump via PoinTT OAuth2.

    Usage:
        api = IVTApi(session, device_id, access_token, refresh_token, expires_at)
        data = await api.get("/heatingCircuits/hc1/roomtemperature")
        await api.put("/heatingCircuits/hc1/temporaryRoomSetpoint", 22.0)
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        device_id: str,
        access_token: str,
        refresh_token: str | None = None,
        token_expires_at: datetime | None = None,
        on_token_refresh: callable = None,
    ):
        """Initialize API client.

        Args:
            session: aiohttp client session
            device_id: PoinTT device/gateway ID
            access_token: OAuth2 access token
            refresh_token: OAuth2 refresh token for auto-renewal
            token_expires_at: When the access token expires
            on_token_refresh: Callback(access_token, refresh_token, expires_at)
                              called after successful token refresh so HA can persist tokens
        """
        self._session = session
        self._device_id = device_id
        self._base_url = f"{POINTT_BASE_URL}{device_id}/resource"
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_expires_at = token_expires_at
        self._on_token_refresh = on_token_refresh
        self._lock = asyncio.Lock()

    # ── Token Management ─────────────────────────────────────

    @property
    def access_token(self) -> str:
        return self._access_token

    @property
    def refresh_token(self) -> str | None:
        return self._refresh_token

    @property
    def token_expires_at(self) -> datetime | None:
        return self._token_expires_at

    def _is_token_expired(self) -> bool:
        """Check if token is expired or expires within 5 minutes."""
        if not self._token_expires_at:
            return bool(self._refresh_token)
        return datetime.now(timezone.utc) >= (
            self._token_expires_at - timedelta(minutes=5)
        )

    async def _refresh_access_token(self):
        """Refresh the access token using the refresh token."""
        if not self._refresh_token:
            raise IVTAuthError("No refresh token available")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
            "client_id": CLIENT_ID,
        }

        try:
            async with self._session.post(TOKEN_URL, data=data) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise IVTAuthError(f"Token refresh failed ({resp.status}): {text}")

                token_data = await resp.json()
                self._access_token = token_data["access_token"]
                if "refresh_token" in token_data:
                    self._refresh_token = token_data["refresh_token"]
                expires_in = token_data.get("expires_in", 3600)
                self._token_expires_at = datetime.now(timezone.utc) + timedelta(
                    seconds=expires_in
                )

                _LOGGER.info("Token refreshed (expires in %ds)", expires_in)

                # Notify HA to persist the new tokens
                if self._on_token_refresh:
                    await self._on_token_refresh(
                        self._access_token,
                        self._refresh_token,
                        self._token_expires_at,
                    )

        except aiohttp.ClientError as err:
            raise IVTConnectionError(f"Token refresh connection error: {err}")

    async def _ensure_token(self):
        """Ensure we have a valid token, refresh if needed."""
        if self._is_token_expired():
            await self._refresh_access_token()

    # ── HTTP Methods ─────────────────────────────────────────

    def _url(self, path: str) -> str:
        """Build full API URL from path."""
        return f"{self._base_url}{path}"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._access_token}"}

    async def get(self, path: str) -> dict | None:
        """GET a value from the API.

        Args:
            path: API path like "/heatingCircuits/hc1/roomtemperature"

        Returns:
            Parsed JSON response dict, or None on error
        """
        await self._ensure_token()
        url = self._url(path)

        try:
            async with self._lock:
                async with self._session.get(
                    url, headers=self._headers(), timeout=30
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 404:
                        _LOGGER.debug("GET %s: not found", path)
                        return None
                    else:
                        text = await resp.text()
                        _LOGGER.warning("GET %s: HTTP %d — %s", path, resp.status, text[:200])
                        return None
        except aiohttp.ClientError as err:
            _LOGGER.error("GET %s: connection error — %s", path, err)
            return None

    async def put(self, path: str, value) -> bool:
        """PUT a value to the API.

        Args:
            path: API path like "/heatingCircuits/hc1/operationMode"
            value: Value to set (string, float, etc.)

        Returns:
            True on success, False on failure
        """
        await self._ensure_token()
        url = self._url(path)
        payload = json.dumps({"value": value})

        try:
            async with self._lock:
                async with self._session.put(
                    url,
                    data=payload,
                    headers={**self._headers(), "Content-Type": "application/json"},
                    timeout=30,
                ) as resp:
                    if resp.status in (200, 204):
                        _LOGGER.info("PUT %s = %s: OK", path, value)
                        return True
                    else:
                        text = await resp.text()
                        _LOGGER.error("PUT %s = %s: HTTP %d — %s", path, value, resp.status, text[:200])
                        return False
        except aiohttp.ClientError as err:
            _LOGGER.error("PUT %s: connection error — %s", path, err)
            return False

    async def get_value(self, path: str):
        """GET and extract just the 'value' field. Returns None if unavailable."""
        data = await self.get(path)
        if data and "value" in data:
            return data["value"]
        return None

    async def get_many(self, paths: list[str]) -> dict:
        """GET multiple paths and return {path: full_response_dict}.

        Runs requests sequentially (K30 doesn't handle parallel well).
        """
        results = {}
        for path in paths:
            results[path] = await self.get(path)
        return results

    # ── Convenience Methods ──────────────────────────────────

    async def test_connection(self) -> bool:
        """Test if we can reach the API and get a valid response."""
        try:
            data = await self.get("/gateway/versionFirmware")
            return data is not None and "value" in data
        except Exception:
            return False

    async def get_device_info(self) -> dict:
        """Get device identification info."""
        paths = [
            "/gateway/versionFirmware",
            "/gateway/versionHardware",
            "/gateway/wifi/ip/ipv4",
            "/heatSources/hs1/type",
            "/heatSources/hs1/heatPumpType",
            "/system/brand",
        ]
        data = await self.get_many(paths)
        return {
            "firmware": (data.get(paths[0]) or {}).get("value"),
            "hardware": (data.get(paths[1]) or {}).get("value"),
            "ip": (data.get(paths[2]) or {}).get("value"),
            "source_type": (data.get(paths[3]) or {}).get("value"),
            "hp_type": (data.get(paths[4]) or {}).get("value"),
            "brand": (data.get(paths[5]) or {}).get("value"),
        }

    # ── OAuth Flow Helpers (for config_flow) ─────────────────

    @staticmethod
    def build_auth_url() -> str:
        """Build the OAuth2 authorization URL for SingleKey ID."""
        import hashlib
        import base64
        import urllib.parse

        challenge = hashlib.sha256(CODE_VERIFIER.encode()).digest()
        challenge_b64 = base64.urlsafe_b64encode(challenge).decode().rstrip("=")

        params = {
            "redirect_uri": urllib.parse.quote_plus(REDIRECT_URI),
            "client_id": CLIENT_ID,
            "response_type": "code",
            "prompt": "login",
            "state": "_yUmSV3AjUTXfn6DSZQZ-g",
            "nonce": "5iiIvx5_9goDrYwxxUEorQ",
            "scope": urllib.parse.quote(" ".join(SCOPES)),
            "code_challenge": challenge_b64,
            "code_challenge_method": "S256",
            "style_id": "tt_bsch",
            "suppressed_prompt": "login",
        }

        query_inner = "&".join(f"{k}={v}" for k, v in params.items())
        callback_path = urllib.parse.quote_plus("/auth/connect/authorize/callback?")
        full_query = f"ReturnUrl={callback_path}{urllib.parse.quote(query_inner)}"

        return f"https://singlekey-id.com/auth/en-us/login?{full_query}"

    @staticmethod
    def extract_code_from_url(url: str) -> str | None:
        """Extract authorization code from OAuth callback URL."""
        import urllib.parse

        if "code=" in url:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            return params.get("code", [None])[0]
        return None

    async def exchange_code_for_tokens(self, code: str) -> dict | None:
        """Exchange authorization code for tokens.

        Returns:
            dict with access_token, refresh_token, expires_at on success, None on failure
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "code_verifier": CODE_VERIFIER,
        }

        try:
            async with self._session.post(TOKEN_URL, data=data) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    _LOGGER.error("Token exchange failed (%d): %s", resp.status, text[:300])
                    return None

                token_data = await resp.json()
                if "access_token" not in token_data:
                    _LOGGER.error("No access_token in response")
                    return None

                expires_in = token_data.get("expires_in", 3600)
                return {
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token"),
                    "expires_at": (
                        datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                    ).isoformat(),
                }
        except Exception as err:
            _LOGGER.error("Token exchange error: %s", err)
            return None
