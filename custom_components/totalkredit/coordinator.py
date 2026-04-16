"""Totalkredit DataUpdateCoordinator og API-hjælpefunktion."""
from __future__ import annotations

import asyncio
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

FIXED_RATE_API_URL = (
    "https://www.totalkredit.dk/api/bondinformation/table"
    "?tableId=privat-udbetaling-af-laan-aktuelle-kurser-kunder&domain=totalkredit"
)
VARIABLE_RATE_API_URL = (
    "https://www.totalkredit.dk/api/bondinformation/table"
    "?tableId=privat-udbetaling-af-variabel-laan-aktuelle-kurser-kunder&domain=totalkredit"
)
TILPASNING_API_URL = (
    "https://www.totalkredit.dk/api/bondinformation/table"
    "?tableId=privat-udbetaling-af-laan-kontantrenter-raadgivere-og-kunder&domain=totalkredit"
)


async def _fetch_raw(session, url: str) -> list[dict]:
    """Hent og flatten obligationer fra én API-URL."""
    async with session.get(url) as response:
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


def _tilpasning_slug(name: str) -> str:
    """Generer stabilt fondCode-slug for tilpasningslån (har ingen fondCode i API)."""
    return (
        "tilpasning_"
        + name.lower()
        .replace("å", "aa")
        .replace("æ", "ae")
        .replace("ø", "oe")
        .replace(" ", "_")
    )


async def fetch_bonds(hass: HomeAssistant) -> list[dict]:
    """Hent alle obligationstyper fra Totalkredit API parallelt."""
    session = async_get_clientsession(hass)

    fixed, variable, tilpasning = await asyncio.gather(
        _fetch_raw(session, FIXED_RATE_API_URL),
        _fetch_raw(session, VARIABLE_RATE_API_URL),
        _fetch_raw(session, TILPASNING_API_URL),
    )

    bonds: list[dict] = list(fixed)

    for bond in variable:
        # F-kort: expectedRate er "Dagens beregningsrente" inkl. rentetillæg — brug som effectiveRate
        bond["effectiveRate"] = bond.pop("expectedRate", "")
        bonds.append(bond)

    for bond in tilpasning:
        # Tilpasningslån har ingen fondCode i API — brug stabilt navne-slug
        bond["fondCode"] = _tilpasning_slug(bond["name"])
        bond["effectiveRate"] = bond.pop("innerInterestGrossValue", "")
        bond["priceRate"] = "100"
        bonds.append(bond)

    return bonds


class TotalkreditCoordinator(DataUpdateCoordinator):
    """Coordinator der holder obligationsdata opdateret."""

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="totalkredit",
            update_interval=None,  # Opdateres via async_track_time_change kl. 08-18
        )

    async def _async_update_data(self) -> list[dict]:
        try:
            return await fetch_bonds(self.hass)
        except Exception as err:
            raise UpdateFailed(f"Fejl ved hentning af Totalkredit data: {err}") from err
