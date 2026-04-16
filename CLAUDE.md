# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Home Assistant custom integration that fetches Danish mortgage bond rates from Totalkredit's API and exposes them as sensor entities. Configured via the HA UI (config flow) — NOT via `configuration.yaml`. Distributed via HACS as a custom repository.

## Before publishing to GitHub

Replace all occurrences of `GITHUB_USERNAME` in `manifest.json` and `README.md` with the actual GitHub username.

## Installation in Home Assistant

1. Copy `custom_components/totalkredit/` into the HA `config/custom_components/` folder.
2. Restart Home Assistant.
3. Go to Settings → Devices & Services → Add Integration → search for "Totalkredit".
4. Select the bonds you want to monitor.

**Do NOT add anything to `configuration.yaml`** — this integration uses config flow only.

## Architecture

- **`sensor.py`** — `TotalkreditSensor` entity; uses `async_setup_entry` (config-flow based).
- **`coordinator.py`** — `TotalkreditCoordinator` (DataUpdateCoordinator) and `fetch_bonds(hass)`. Uses HA's managed aiohttp session via `async_get_clientsession`.
- **`config_flow.py`** — `TotalkreditConfigFlow` (initial setup) and `TotalkreditOptionsFlow` (edit bond selection). `OptionsFlow` uses `self.config_entry` (no constructor arg).
- **`__init__.py`** — `async_setup_entry` / `async_unload_entry`. Uses `async_config_entry_first_refresh()` for initial data load; daily refresh at 10:00 via `async_track_time_change`.
- **`const.py`** — `DOMAIN` and `PLATFORMS = [Platform.SENSOR]`.
- **`manifest.json`** — integration metadata; `config_flow: true`.

### Data flow

`async_setup_entry` → `async_config_entry_first_refresh()` → `fetch_bonds(hass)` → creates one `TotalkreditSensor` per selected bond → `async_track_time_change` triggers daily refresh at 10:00.

### API

```
GET https://www.totalkredit.dk/api/bondinformation/table
    ?tableId=privat-udbetaling-af-laan-aktuelle-kurser-kunder&domain=totalkredit
```

Response structure: `{ groups: [{ name, entries: [{ name, fondCode, priceRate, effectiveRate, spotPriceRatePayment, lifetime, openForOffer, isOpenForOffer, nasdaqUrl }] }] }`

### Entities

- **State** (`native_value`): `priceRate` parsed as float (Danish decimal comma → dot). `None` if empty.
- **Attributes**: all bond fields (`navn`, `løbetid`, `fondskode`, `åben_for_tilbud`, `er_åben_for_tilbud`, `effektiv_rente`, `aktuel_kurs`, `gruppe`, `nasdaq_url`).
- **`unique_id`**: `totalkredit_{fondCode}`
- **Name**: `Totalkredit {bond name}` (e.g., `Totalkredit 4% 2056 med afdrag`)
