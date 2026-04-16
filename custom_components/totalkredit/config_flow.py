"""Config flow og options flow for Totalkredit."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    SelectSelector,
    SelectSelectorConfig,
)

from .const import DOMAIN
from .coordinator import fetch_bonds


def _build_schema(
    options: list[dict],
    current: list[str],
) -> vol.Schema:
    """Byg formular-schema med vælg/fravælg-alle toggles og obligationsvælger."""
    return vol.Schema(
        {
            vol.Optional("select_all", default=False): BooleanSelector(),
            vol.Optional("deselect_all", default=False): BooleanSelector(),
            vol.Required("selected_bonds", default=current): SelectSelector(
                SelectSelectorConfig(options=options, multiple=True)
            ),
        }
    )


class TotalkreditConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Håndterer første opsætning via UI."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        try:
            bonds = await fetch_bonds(self.hass)
        except Exception:
            return self.async_abort(reason="cannot_connect")

        all_codes = [b["fondCode"] for b in bonds]
        options = [{"value": b["fondCode"], "label": b["name"]} for b in bonds]
        current: list[str] = []

        if user_input is not None:
            if user_input.get("select_all"):
                current = all_codes
            elif user_input.get("deselect_all"):
                current = []
            elif not user_input.get("selected_bonds"):
                errors["selected_bonds"] = "no_selection"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Totalkredit",
                    data={"selected_bonds": user_input["selected_bonds"]},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(options, current),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> TotalkreditOptionsFlow:
        return TotalkreditOptionsFlow()


class TotalkreditOptionsFlow(config_entries.OptionsFlow):
    """Håndterer ændring af obligationsvalg efter opsætning."""

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        try:
            bonds = await fetch_bonds(self.hass)
        except Exception:
            return self.async_abort(reason="cannot_connect")

        all_codes = [b["fondCode"] for b in bonds]
        options = [{"value": b["fondCode"], "label": b["name"]} for b in bonds]
        current: list[str] = self.config_entry.options.get(
            "selected_bonds",
            self.config_entry.data.get("selected_bonds", []),
        )

        if user_input is not None:
            if user_input.get("select_all"):
                current = all_codes
            elif user_input.get("deselect_all"):
                current = []
            elif not user_input.get("selected_bonds"):
                errors["selected_bonds"] = "no_selection"
            else:
                return self.async_create_entry(
                    title="",
                    data={"selected_bonds": user_input["selected_bonds"]},
                )

        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(options, current),
            errors=errors,
        )
