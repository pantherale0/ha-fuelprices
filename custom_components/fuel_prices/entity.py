"""Fuel Price entity base type."""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import FuelPricesCoordinator


class FuelStationEntity(CoordinatorEntity):
    """Represents a fuel station."""

    def __init__(
        self, coordinator: FuelPricesCoordinator, fuel_station_id, entity_id, source
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.coordinator: FuelPricesCoordinator = coordinator
        self._fuel_station_id = fuel_station_id
        self._entity_id = entity_id
        self._fuel_station_source = str(source).lower()

    @property
    def _fuel_station(self):
        """Return the fuel station."""
        return self.coordinator.api.configured_sources[
            self._fuel_station_source
        ].location_cache[self._fuel_station_id]

    @property
    def unique_id(self) -> str | None:
        """Return unique ID."""
        return f"fuelprices_{self._fuel_station_id}_{self._entity_id}"
