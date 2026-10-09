"""Fuel Price entity base type."""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from pyfuelprices.fuel_locations import FuelLocation

from .coordinator import FuelPricesCoordinator


class FuelStationEntity(CoordinatorEntity):
    """Represents a fuel station."""

    config: ConfigEntry

    def __init__(
        self, coordinator: FuelPricesCoordinator, fuel_station_id, entity_id, source, area, state_value, config: ConfigEntry
    ) -> None:
        """Initialize."""
        self.config = config
        super().__init__(coordinator)
        self.coordinator: FuelPricesCoordinator = coordinator
        self._fuel_station_id = fuel_station_id
        self._entity_id = entity_id
        self._fuel_station_source = str(source).lower()
        self.area = area
        self.state_value = state_value

    @property
    def _fuel_station(self) -> FuelLocation | None:
        """Return the fuel station, or None if it is no longer known to its source."""
        source = self.coordinator.api.configured_sources.get(
            self._fuel_station_source)
        if source is None:
            return None
        return source.location_cache.get(self._fuel_station_id)

    @property
    def available(self) -> bool:
        """Return if the fuel station is available."""
        return super().available and self._fuel_station is not None

    @property
    def unique_id(self) -> str | None:
        """Return unique ID."""
        return f"fuelprices_{self._fuel_station_id}_{self._entity_id}"
