"""Config flow og options flow for Totalkredit."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

from .const import DOMAIN
from .coordinator import fetch_bonds


class TotalkreditConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Håndterer første opsætning via UI."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get("selected_bonds"):
                errors["selected_bonds"] = "no_selection"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Totalkredit",
                    data={"selected_bonds": user_input["selected_bonds"]},
                )

        try:
            bonds = await fetch_bonds()
        except Exception:
            return self.async_abort(reason="cannot_connect")

        options = [{"value": b["fondCode"] or b.get("name"), "label": b["name"]} for b in bonds]

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("selected_bonds"): SelectSelector(
                        SelectSelectorConfig(options=options, multiple=True)
                    )
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> TotalkreditOptionsFlow:
        return TotalkreditOptionsFlow(config_entry)


class TotalkreditOptionsFlow(config_entries.OptionsFlow):
    """Håndterer ændring af obligationsvalg efter opsætning."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get("selected_bonds"):
                errors["selected_bonds"] = "no_selection"
            else:
                return self.async_create_entry(title="", data=user_input)

        try:
            bonds = await fetch_bonds()
        except Exception:
            return self.async_abort(reason="cannot_connect")

        current = self._config_entry.options.get(
            "selected_bonds",
            self._config_entry.data.get("selected_bonds", []),
        )
        options = [{"value": b.get("fondCode") or b.get("name"), "label": b["name"]} for b in bonds]

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("selected_bonds", default=current): SelectSelector(
                        SelectSelectorConfig(options=options, multiple=True)
                    )
                }
            ),
            errors=errors,
        )
