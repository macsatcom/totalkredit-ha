# Totalkredit Home Assistant Integration

Home Assistant integration der henter aktuelle obligationskurser fra [Totalkredit](https://www.totalkredit.dk) og eksponerer dem som sensor-entities.

## Installation via HACS

1. Åbn HACS i Home Assistant
2. Gå til **Integrations** → menuikonet → **Custom repositories**
3. Tilføj URL: `https://github.com/macsatcom/totalkredit-ha` med kategori **Integration**
4. Find "Totalkredit" i HACS og installér
5. Genstart Home Assistant

## Manuel installation

Kopier mappen `custom_components/totalkredit/` til din Home Assistant `config/custom_components/` mappe og genstart.

## Konfiguration

Integrationen konfigureres via Home Assistant UI:

1. Gå til **Indstillinger** → **Enheder & tjenester** → **Tilføj integration**
2. Søg efter "Totalkredit"
3. Vælg de obligationer du ønsker at følge fra listen
4. Gem — sensorer oprettes automatisk

Du kan til enhver tid ændre dit obligationsvalg via **Konfigurer** på integrationssiden.

## Entities

| Entity | Eksempel |
|--------|---------|
| `sensor.totalkredit_4_2056_med_afdrag` | `99.16` |

**State:** `priceRate` (udbetalingskurs) som decimaltal. Vises som `unavailable` hvis obligationen ikke har en kurs (typisk lukkede obligationer).

**Attributter:**

| Attribut | Beskrivelse |
|----------|-------------|
| `navn` | Obligationens navn |
| `løbetid` | Lånets maksimale løbetid |
| `fondskode` | Unik fondskode (Nasdaq Copenhagen) |
| `åben_for_tilbud` | "Åben" eller "Lukket" |
| `er_åben_for_tilbud` | `true` / `false` |
| `effektiv_rente` | Effektiv rente inkl. kursfradrag |
| `aktuel_kurs` | Aktuel spotpris ved udbetaling |
| `gruppe` | Obligationsgruppe (f.eks. "Fast rente") |
| `nasdaq_url` | Link til Nasdaq Copenhagen |

## Opdatering

Data hentes dagligt kl. 10:00 fra Totalkredits API.

## Fejlfinding

**HA starter ikke / integrationen loader ikke:**
- Kontrollér at du **ikke** har `sensor: - platform: totalkredit` i din `configuration.yaml` — denne integration understøtter udelukkende UI-konfiguration.
- Slet eventuelle gamle YAML-linjer, genstart HA, og tilføj integrationen via Indstillinger → Enheder & tjenester.
