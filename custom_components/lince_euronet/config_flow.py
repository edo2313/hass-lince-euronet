"""Config flow for the Lince Euronet integration."""

from __future__ import annotations

import asyncio
import binascii
import logging
import socket
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional("code"): vol.Coerce(str),
    }
)


class PlaceholderHub:
    """Placeholder class to make tests pass."""

    def __init__(self, host: str, port: int = 80) -> None:
        """Initialize."""
        self.host = host
        self.port = port

    async def authenticate(self, username: str, password: str) -> bool:
        """Test if we can authenticate with the host using HTTP Basic Auth."""
        url = f"http://{self.host}:{self.port}/"
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                resp_coro = session.get(url, auth=aiohttp.BasicAuth(username, password))
                async with await resp_coro as resp:
                    return resp.status == 200
        except (aiohttp.ClientError, TimeoutError, OSError, ValueError):
            return False


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    # Parse host and port
    host = data[CONF_HOST]
    if ":" in host:
        host, port_str = host.rsplit(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            port = 80
    else:
        port = 80
    hub = PlaceholderHub(host, port)
    if not await hub.authenticate(data[CONF_USERNAME], data[CONF_PASSWORD]):
        raise InvalidAuth
    return {"title": host}


class LinceEuronetConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Lince Euronet."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        discovered_host = None
        discovered_mac = None
        discovered_http_port = None
        # Only run autodiscovery if the form is being shown, not after submit
        if user_input is None:
            try:
                loop = asyncio.get_running_loop()
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.settimeout(3)
                payload = binascii.unhexlify("07784575726f4e4554000a")
                sock.sendto(payload, ("255.255.255.255", 30303))
                data, addr = await loop.run_in_executor(None, sock.recvfrom, 1024)
                response = data.decode()
                if response.startswith("EURONET\r\n"):
                    lines = response.split("\r\n")
                    discovered_mac = lines[1].strip()
                    discovered_http_port = lines[3].strip()
                    discovered_host = addr[0]
            except (OSError, ValueError):
                _LOGGER.debug("Autodiscovery failed or no device found")
        if user_input is not None:
            code = user_input.get("code")
            if code is not None and (len(code) != 6 or not code.isdigit()):
                errors["code"] = "invalid_code"
            else:
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()
                try:
                    info = await validate_input(self.hass, user_input)
                except InvalidAuth:
                    errors["base"] = "invalid_auth"
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"
                else:
                    return self.async_create_entry(title=info["title"], data=user_input)
            # If there are errors, re-show the form with previous input
            schema = STEP_USER_DATA_SCHEMA
            placeholders = None
            if discovered_host:
                schema = vol.Schema(
                    {
                        vol.Required(CONF_HOST, default=discovered_host): str,
                        vol.Required(
                            CONF_USERNAME, default=user_input.get(CONF_USERNAME, "")
                        ): str,
                        vol.Required(
                            CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, "")
                        ): str,
                        vol.Optional(
                            "code", default=user_input.get("code", "")
                        ): vol.Coerce(str),
                    }
                )
                placeholders = {
                    "mac": discovered_mac or "",
                    "http_port": discovered_http_port or "",
                }
            else:
                schema = vol.Schema(
                    {
                        vol.Required(
                            CONF_HOST, default=user_input.get(CONF_HOST, "")
                        ): str,
                        vol.Required(
                            CONF_USERNAME, default=user_input.get(CONF_USERNAME, "")
                        ): str,
                        vol.Required(
                            CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, "")
                        ): str,
                        vol.Optional(
                            "code", default=user_input.get("code", "")
                        ): vol.Coerce(str),
                    }
                )
            return self.async_show_form(
                step_id="user",
                data_schema=schema,
                errors=errors,
                description_placeholders=placeholders,
            )
        # If autodiscovery succeeded, pre-fill the form
        schema = STEP_USER_DATA_SCHEMA
        placeholders = None
        if discovered_host:
            schema = vol.Schema(
                {
                    vol.Required(CONF_HOST, default=discovered_host): str,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional("code"): vol.Coerce(str),
                }
            )
            placeholders = {
                "mac": discovered_mac or "",
                "http_port": discovered_http_port or "",
            }
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders=placeholders,
        )


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
