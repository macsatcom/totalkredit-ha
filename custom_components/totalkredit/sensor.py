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

    async_add_entities(
        TotalkreditSensor(coordinator, bond)
        for bond in (coordinator.data or [])
        if bond.get("fondCode") or bond.get("name") in selected
    )


class TotalkreditSensor(CoordinatorEntity, SensorEntity):
    """Sensor der repræsenterer én Totalkredit obligation."""

    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: TotalkreditCoordinator, bond: dict) -> None:
        super().__init__(coordinator)
        self._fond_code = bond["fondCode"] or bond.get("name")
        self._attr_unique_id = f"totalkredit_{self._fond_code}"
        self._attr_name = f"Totalkredit {bond['name']}"

    def _get_bond(self) -> dict | None:
        if not self.coordinator.data:
            return None
        return next(
            (b for b in self.coordinator.data if (b.get("fondCode") == self._fond_code or b.get("name") == self._fond_code)),
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
        try:
            return float(price_rate.replace(",", "."))
        except ValueError:
            return None

    @property
    def extra_state_attributes(self) -> dict:
        """Returner alle obligationsfelter som attributter."""
        bond = self._get_bond()
        if bond is None:
            return {}
        return {
            "navn": bond.get("name"),
            "løbetid": bond.get("lifetime"),
            "fondskode": bond.get("fondCode"),
            "åben_for_tilbud": bond.get("openForOffer"),
            "er_åben_for_tilbud": bond.get("isOpenForOffer"),
            "effektiv_rente": bond.get("effectiveRate") or bond.get("expectedRate") or bond.get("innerInterestGrossValue"),
            "aktuel_kurs": bond.get("spotPriceRatePayment"),
            "gruppe": bond.get("group"),
            "nasdaq_url": bond.get("nasdaqUrl"),
        }
