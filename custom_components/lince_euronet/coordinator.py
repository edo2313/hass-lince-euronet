"""Coordinator for Lince Euronet integration.

Handles polling and data updates from status.xml for all sensor types.
"""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
import re

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import LinceEuronetApi


class LinceEuronetCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch status.xml once per type and update entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: LinceEuronetApi,
    ) -> None:
        """Initialize the coordinator with API and status type."""
        super().__init__(
            hass,
            logger=logging.getLogger(__name__),
            name="lince_euronet",
            config_entry=config_entry,
            update_interval=timedelta(seconds=10),
            always_update=True,
        )
        self.api = api

    async def _async_update_data(self):
        """Fetch data from the Lince Euronet device."""
        try:
            async with asyncio.timeout(10):
                result = {}

                # Get system state
                xml = await self.api.get_xml(payload="Sta=")
                result["system_state"] = self.api.parse_in_state_system(xml)

                # Parse <gstate> for system state
                gstate_match = re.search(r"<gstate>([^<]*)</gstate>", xml)
                gstate = gstate_match.group(1) if gstate_match else ""
                result["g_state"] = gstate

                # Get ingressi state
                xml = await self.api.get_xml(payload="Ing=0")
                result["ingressi_state"] = self.api.parse_in_state_ingressi(xml)

                return result
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
