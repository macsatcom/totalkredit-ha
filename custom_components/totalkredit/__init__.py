"""Totalkredit integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_change

from .const import DOMAIN, PLATFORMS
from .coordinator import TotalkreditCoordinator

# Opdater hver time fra kl. 08:00 til 18:00
UPDATE_HOURS = range(8, 19)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Opsæt integration fra en config entry."""
    coordinator = TotalkreditCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    async def _async_update(now) -> None:
        await coordinator.async_refresh()

    for hour in UPDATE_HOURS:
        entry.async_on_unload(
            async_track_time_change(hass, _async_update, hour=hour, minute=0, second=0)
        )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Genindlæs entry når options ændres."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Afmonter integration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
