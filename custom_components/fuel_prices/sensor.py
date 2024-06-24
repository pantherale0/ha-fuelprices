"""Sensor for fuel prices."""

from __future__ import annotations


import logging

from collections.abc import Mapping
from typing import Any
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_RADIUS, CONF_NAME, STATE_UNKNOWN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pyfuelprices.const import PROP_FUEL_LOCATION_SOURCE
from .const import CONF_AREAS, DOMAIN, CONF_STATE_VALUE, CONF_CHEAPEST_SENSORS, CONF_CHEAPEST_SENSORS_COUNT, CONF_CHEAPEST_SENSORS_FUEL_TYPE
from .entity import FuelStationEntity, CheapestFuelEntity
from .coordinator import FuelPricesCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Integration platform creation."""
    cooridinator: FuelPricesCoordinator = hass.data[DOMAIN][entry.entry_id]
    areas = entry.options.get(CONF_AREAS, entry.data.get(CONF_AREAS, []))
    entities = []
    found_entities = []
    state_value = entry.options.get(
        CONF_STATE_VALUE, entry.data.get(CONF_STATE_VALUE, "name")
    )
    for area in areas:
        _LOGGER.debug("Registering entities for area %s", area[CONF_NAME])
        for station in await cooridinator.api.find_fuel_locations_from_point(
            coordinates=(area[CONF_LATITUDE], area[CONF_LONGITUDE]),
            radius=area[CONF_RADIUS],
        ):
            if station["id"] not in found_entities:
                entities.append(
                    FeulStationTracker(
                        coordinator=cooridinator,
                        fuel_station_id=station["id"],
                        entity_id="devicetracker",
                        source=station["props"][PROP_FUEL_LOCATION_SOURCE],
                        area=area[CONF_NAME],
                        state_value=state_value
                    )
                )
                found_entities.append(station["id"])
        if area[CONF_CHEAPEST_SENSORS]:
            _LOGGER.debug("Registering %s cheapest entities for area %s",
                          area[CONF_CHEAPEST_SENSORS_COUNT],
                          area[CONF_NAME])
            for x in range(0, int(area[CONF_CHEAPEST_SENSORS_COUNT]), 1):
                entities.append(CheapestFuelSensor(
                    coordinator=cooridinator,
                    count=x+1,
                    area=area[CONF_NAME],
                    fuel=area[CONF_CHEAPEST_SENSORS_FUEL_TYPE],
                    coords=(area[CONF_LATITUDE], area[CONF_LONGITUDE]),
                    radius=area[CONF_RADIUS]
                ))
    async_add_entities(entities, True)


class FeulStationTracker(FuelStationEntity, SensorEntity):
    """A fuel station entity."""

    @property
    def native_value(self) -> str:
        """Return the native value of the entity."""
        if self.state_value == "name":
            return self._fuel_station.name
        return self._get_fuels.get(self.state_value, self._fuel_station.name)

    @property
    def _get_fuels(self) -> dict:
        """Return list of fuels."""
        output = {}
        for fuel in self._fuel_station.available_fuels:
            output[fuel.fuel_type] = fuel.cost
        return output

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return extra state attributes."""
        return {
            **self._fuel_station.__dict__(),
            **self._get_fuels,
            "area": self.area
        }

    @property
    def icon(self) -> str:
        """Return entity icon."""
        return "mdi:gas-station"

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._fuel_station.name

    @property
    def native_unit_of_measurement(self) -> str:
        """Return unit of measurement."""
        if isinstance(self.native_value, str):
            return None
        return self._fuel_station.currency.upper()

    @property
    def state_class(self) -> str:
        """Return state type."""
        if isinstance(self.native_value, str):
            return None
        return "total"


class CheapestFuelSensor(CheapestFuelEntity, SensorEntity):
    """A entity that shows the cheapest fuel for an area."""

    _attr_should_poll = True  # we need to query the module for this data
    _last_update = None
    _next_update = datetime.now()
    _cached_data = None

    async def async_update(self) -> None:
        """Update device data."""
        if (self._last_update is not None) and (
            self._next_update > datetime.now()
        ):
            return True
        data = await self.coordinator.api.find_fuel_from_point(
            coordinates=self._coords,
            fuel_type=self._fuel,
            radius=self._radius
        )
        if len(data) >= (int(self._count)-1):
            self._cached_data = data[int(self._count)-1]
            return True
        self._cached_data = None
        self._next_update = datetime.now() + timedelta(days=1)

    @property
    def native_value(self) -> str | float:
        """Return state of entity."""
        if self._cached_data is not None:
            return self._cached_data["cost"]
        return STATE_UNKNOWN

    @property
    def name(self) -> str:
        """Name of the entity."""
        return f"{self._area} cheapest {self._fuel} {self._count}"

    @property
    def state_class(self) -> str:
        """Return state type."""
        if isinstance(self.native_value, float):
            return "total"
        return None

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return extra state attributes."""
        return {
            "area": self._area,
            **self._cached_data
        }
