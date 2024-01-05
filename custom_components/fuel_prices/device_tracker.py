"""Device tracker for fuel prices."""
from __future__ import annotations

import logging
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_RADIUS, CONF_NAME
from homeassistant.components.device_tracker.config_entry import (
    BaseTrackerEntity,
    SourceType,
    ATTR_SOURCE_TYPE,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from pyfuelprices.const import PROP_FUEL_LOCATION_SOURCE
from .const import CONF_AREAS, DOMAIN
from .entity import FeulStationEntity
from .coordinator import FuelPricesCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setup fuel prices device tracker component."""
    cooridinator: FuelPricesCoordinator = hass.data[DOMAIN][entry.entry_id]
    areas = entry.data[CONF_AREAS]
    entities = []
    found_entities = []
    for area in areas:
        _LOGGER.debug("Registering entities for area %s", area[CONF_NAME])
        for station in await cooridinator.api.find_fuel_locations_from_point(
            coordinates=(area[CONF_LATITUDE], area[CONF_LONGITUDE]),
            radius=area[CONF_RADIUS],
        ):
            if station.id not in found_entities:
                entities.append(
                    FeulStationTracker(
                        coordinator=cooridinator,
                        fuel_station_id=station.id,
                        entity_id="devicetracker",
                        source=station.props[PROP_FUEL_LOCATION_SOURCE],
                    )
                )
                found_entities.append(station.id)

    async_add_entities(entities, True)


class FeulStationTracker(FeulStationEntity, BaseTrackerEntity):
    """A fuel station tracker entity."""

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._fuel_station.name

    @property
    def location_accuracy(self) -> int:
        """Return the location accuracy of the device.

        Value in meters.
        """
        return 0

    @property
    def state(self) -> str | None:
        """Return the state of the device."""
        if self.location_name is not None:
            return self.location_name

    @property
    def _get_fuels(self) -> dict:
        """Return list of fuels."""
        output = {}
        for fuel in self._fuel_station.available_fuels:
            output[fuel.fuel_type] = fuel.cost
        return output

    @property
    def latitude(self) -> float:
        """Return the latitude."""
        return self._fuel_station.lat

    @property
    def longitude(self) -> float:
        """Return the longitude."""
        return self._fuel_station.long

    @property
    def location_name(self) -> str:
        """Return the name of the location."""
        return self._fuel_station.name

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.GPS

    @property
    def state_attributes(self) -> dict[str, StateType]:
        """Return the fuel location prices."""
        attr: dict[str, StateType] = {
            ATTR_SOURCE_TYPE: self.source_type,
            **self._get_fuels,
            **self._fuel_station.__dict__(),
        }
        if self.latitude is not None and self.longitude is not None:
            attr[ATTR_LATITUDE] = self.latitude
            attr[ATTR_LONGITUDE] = self.longitude

        return attr
