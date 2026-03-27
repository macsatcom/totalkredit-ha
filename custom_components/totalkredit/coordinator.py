"""Totalkredit DataUpdateCoordinator og API-hjælpefunktion."""
from __future__ import annotations

import logging

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

FIXED_RATE_BONDS_API_URL = (
    "https://www.totalkredit.dk/api/bondinformation/table"
    "?tableId=privat-udbetaling-af-laan-aktuelle-kurser-kunder&domain=totalkredit"
)

N_YEARS_FIXED_RATE_BONDS_API_URL = (
    "https://www.totalkredit.dk/api/bondinformation/table?tableId=privat-udbetaling-af-laan-kontantrenter-raadgivere-og-kunder&domain=totalkredit"
)

VARIABLE_RATE_BONDS_API_URL = (
    "https://www.totalkredit.dk/api/bondinformation/table?tableId=privat-udbetaling-af-variabel-laan-aktuelle-kurser-kunder&domain=totalkredit"
)

async def fetch_bonds_from_url(url: str) -> list[dict]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json(content_type=None)

    bonds = []
    for group in data.get("groups", []):
        group_name = group.get("name", "")
        for entry in group.get("entries", []):
            bond = dict(entry)
            bond["group"] = group_name
            # F-kort
            if group_name == "F-kort":
                bond["name"] = "F-kort"
                bond["effectiveRate"] = bond["expectedRate"]
                bond.pop("expectedRate", None)
            # F3 or F5
            elif "fondCode" not in bond:
                bond["name"] = group_name + " - " + bond["name"]
                bond["fondCode"] = bond["name"]
                bond["effectiveRate"] = bond["innerInterestGrossValue"]
                bond.pop("innerInterestGrossValue", None)
                bond["spotPriceRatePayment"] = "100"

            rate = bond["effectiveRate"].replace("%", "").replace(",", ".").strip()
            bond["effectiveRate"] = f"{round(float(rate), 2):.2f}"



            bonds.append(bond)
    return bonds

async def fetch_bonds() -> list[dict]:
    """Hent alle obligationer fra Totalkredit API."""
    variable_rate_bonds = await fetch_bonds_from_url(VARIABLE_RATE_BONDS_API_URL)
    fixed_rate_bonds = await fetch_bonds_from_url(FIXED_RATE_BONDS_API_URL)
    n_years_fixed_rate_bonds = await fetch_bonds_from_url(N_YEARS_FIXED_RATE_BONDS_API_URL)

    return fixed_rate_bonds + variable_rate_bonds + n_years_fixed_rate_bonds


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
            return await fetch_bonds()
        except Exception as err:
            raise UpdateFailed(f"Fejl ved hentning af Totalkredit data: {err}") from err
