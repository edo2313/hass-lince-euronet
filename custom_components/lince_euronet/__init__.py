"""The Lince Euronet integration."""

from __future__ import annotations

import logging
import re

import aiohttp
from bs4 import BeautifulSoup

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

_PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]


class LinceEuronetApi:
    """Placeholder API class for Lince Euronet integration."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        code: str | None = None,
        port: int = 80,
    ) -> None:
        """Initialize the API with host, username, password, and optional code."""
        self.host = host
        self.username = username
        self.password = password
        self.code = code
        self.port = port

    async def async_test_connection(self) -> bool:
        """Simulate testing connection to the device."""
        return True

    async def get_xml(self, payload: str) -> str:
        """Fetch status.xml."""
        url = f"http://{self.host}:{self.port}/status.xml"
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            resp_coro = session.post(
                url,
                data=payload,
                auth=aiohttp.BasicAuth(self.username, self.password),
            )
            async with await resp_coro as resp:
                xml = await resp.text()
        logging.getLogger(__name__).debug(
            "LinceEuronet: Fetched status.xml with payload '%s'", payload
        )
        return xml

    async def async_get_ingressi_config(self) -> list[str]:
        """Fetch and parse ingressi-filari.html, return sensor names dynamically."""
        url = f"http://{self.host}:{self.port}/ingressi-filari.html"
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            resp_coro = session.get(
                url, auth=aiohttp.BasicAuth(self.username, self.password)
            )
            async with await resp_coro as resp:
                html = await resp.text()
        soup = BeautifulSoup(html, "html.parser")
        # Dynamically extract sensor names from the first column
        names = []
        for th in soup.select("table.table tbody th[bgcolor]"):
            name = th.text.strip()
            # Remove leading number and dash if present
            name = name.split("-", 1)[-1].strip() if "-" in name else name
            names.append(name)
        return names

    def parse_in_state_ingressi(self, xml: str) -> list[int]:
        """Parse <in_state> for ingressi sensors."""
        match = re.search(r"<in_state>([\d,]+)</in_state>", xml)
        if not match:
            return [0] * 5
        values = match.group(1).rstrip(",").split(",")
        in_state = [int(v) if v else 0 for v in values]
        while len(in_state) < 5:
            in_state.append(0)
        return in_state

    def parse_in_state_system(self, xml: str) -> list[int]:
        """Parse <in_state> for system status sensors."""
        match = re.search(r"<in_state>([\d%]+)</in_state>", xml)
        if not match:
            return [0] * 10
        values = match.group(1).split("%")
        in_state = [int(v) if v else 0 for v in values]
        while len(in_state) < 10:
            in_state.append(0)
        return in_state


type LinceEuronetConfigEntry = ConfigEntry[LinceEuronetApi]


async def async_setup_entry(
    hass: HomeAssistant, entry: LinceEuronetConfigEntry
) -> bool:
    """Set up Lince Euronet from a config entry."""
    # Create API instance using config entry data
    api = LinceEuronetApi(
        entry.data["host"],
        entry.data["username"],
        entry.data["password"],
        entry.data.get("code"),
    )
    # Simulate connection test
    if not await api.async_test_connection():
        return False
    entry.runtime_data = api
    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: LinceEuronetConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
