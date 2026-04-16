"""Totalkredit sensor platform."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TotalkreditCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Opret sensorer for de valgte obligationer."""
    coordinator: TotalkreditCoordinator = hass.data[DOMAIN][entry.entry_id]

    selected: list[str] = entry.options.get(
        "selected_bonds", entry.data.get("selected_bonds", [])
    )

    entities = []
    for bond in coordinator.data or []:
        if bond.get("fondCode") in selected:
            entities.append(TotalkreditSensor(coordinator, bond))
            entities.append(TotalkreditInterestSensor(coordinator, bond))

    async_add_entities(entities)


def _parse_rate(value: str) -> float | None:
    """Parser en rentesti som '4,30 %' eller '4.30' til float."""
    try:
        return float(str(value).replace("%", "").replace(",", ".").strip())
    except (ValueError, AttributeError):
        return None


class TotalkreditSensor(CoordinatorEntity, SensorEntity):
    """Sensor der repræsenterer udbetalingskursen for én Totalkredit obligation."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: TotalkreditCoordinator, bond: dict) -> None:
        super().__init__(coordinator)
        self._fond_code = bond["fondCode"]
        self._attr_unique_id = f"totalkredit_{self._fond_code}"
        self._attr_name = f"Totalkredit {bond['name']}"

    def _get_bond(self) -> dict | None:
        if not self.coordinator.data:
            return None
        return next(
            (b for b in self.coordinator.data if b.get("fondCode") == self._fond_code),
            None,
        )

    @property
    def native_value(self) -> float | None:
        """Returner priceRate som sensorens state."""
        bond = self._get_bond()
        if bond is None:
            return None
        price_rate = bond.get("priceRate", "")
        if not price_rate:
            return None
        return _parse_rate(price_rate)

    @property
    def extra_state_attributes(self) -> dict:
        """Returner alle obligationsfelter som attributter."""
        bond = self._get_bond()
        if bond is None:
            return {}
        attrs = {
            "navn": bond.get("name"),
            "løbetid": bond.get("lifetime"),
            "fondskode": bond.get("fondCode"),
            "åben_for_tilbud": bond.get("openForOffer"),
            "er_åben_for_tilbud": bond.get("isOpenForOffer"),
            "effektiv_rente": bond.get("effectiveRate"),
            "aktuel_kurs": bond.get("spotPriceRatePayment"),
            "gruppe": bond.get("group"),
            "nasdaq_url": bond.get("nasdaqUrl"),
        }
        if bond.get("interestMarginRate") is not None:
            attrs["rentetillæg"] = bond["interestMarginRate"]
        return attrs


class TotalkreditInterestSensor(CoordinatorEntity, SensorEntity):
    """Sensor der repræsenterer den effektive rente for én Totalkredit obligation."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "%"

    def __init__(self, coordinator: TotalkreditCoordinator, bond: dict) -> None:
        super().__init__(coordinator)
        self._fond_code = bond["fondCode"]
        self._attr_unique_id = f"totalkredit_rente_{self._fond_code}"
        self._attr_name = f"Totalkredit Rente {bond['name']}"

    def _get_bond(self) -> dict | None:
        if not self.coordinator.data:
            return None
        return next(
            (b for b in self.coordinator.data if b.get("fondCode") == self._fond_code),
            None,
        )

    @property
    def native_value(self) -> float | None:
        """Returner effektiv rente som sensorens state.

        For F-kort er effectiveRate (expectedRate) allerede inkl. rentetillæg.
        For faste obligationer og tilpasningslån bruges effectiveRate direkte.
        """
        bond = self._get_bond()
        if bond is None:
            return None
        return _parse_rate(bond.get("effectiveRate", ""))
