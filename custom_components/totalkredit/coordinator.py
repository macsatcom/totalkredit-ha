"""Totalkredit DataUpdateCoordinator og API-hjælpefunktion."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

API_URL = (
    "https://www.totalkredit.dk/api/bondinformation/table"
    "?tableId=privat-udbetaling-af-laan-aktuelle-kurser-kunder&domain=totalkredit"
)


async def fetch_bonds(hass: HomeAssistant) -> list[dict]:
    """Hent alle obligationer fra Totalkredit API."""
    session = async_get_clientsession(hass)
    async with session.get(API_URL) as response:
        response.raise_for_status()
        data = await response.json(content_type=None)

    bonds = []
    for group in data.get("groups", []):
        group_name = group.get("name", "")
        for entry in group.get("entries", []):
            bond = dict(entry)
            bond["group"] = group_name
            bonds.append(bond)
    return bonds


class TotalkreditCoordinator(DataUpdateCoordinator):
    """Coordinator der holder obligationsdata opdateret."""

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="totalkredit",
            update_interval=None,  # Opdateres via async_track_time_change kl. 10:00
        )

    async def _async_update_data(self) -> list[dict]:
        try:
            return await fetch_bonds(self.hass)
        except Exception as err:
            raise UpdateFailed(f"Fejl ved hentning af Totalkredit data: {err}") from err
