"""Sensor for fuel prices."""

from __future__ import annotations


import logging

from collections.abc import Mapping
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_RADIUS, CONF_NAME
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pyfuelprices.const import PROP_FUEL_LOCATION_SOURCE
from .const import CONF_AREAS, DOMAIN, CONF_STATE_VALUE
from .entity import FuelStationEntity
from .coordinator import FuelPricesCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Integration platform creation."""
    cooridinator: FuelPricesCoordinator = hass.data[DOMAIN][entry.entry_id]
    areas = entry.data[CONF_AREAS]
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
    def device_class(self) -> SensorDeviceClass:
        """Return type of entity."""
        if self.state_value == "name":
            return None
        return SensorDeviceClass.MONETARY

    @property
    def native_unit_of_measurement(self) -> str:
        """Return unit of measurement."""
        if self.state_value == "name":
            return None
        return self._fuel_station.currency.upper()

    @property
    def state_class(self) -> str:
        """Return state type."""
        if self.state_value == "name":
            return None
        return "total"
