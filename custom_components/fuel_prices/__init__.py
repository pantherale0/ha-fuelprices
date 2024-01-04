"""Fuel Prices integration."""

import logging

from pyfuelprices import FuelPrices
from pyfuelprices.const import PROP_AREA_LAT, PROP_AREA_LONG, PROP_AREA_RADIUS

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_LATITUDE, CONF_LONGITUDE, CONF_RADIUS
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, CONF_AREAS, CONF_SOURCES
from .coordinator import FuelPricesCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.DEVICE_TRACKER]


def _build_configured_areas(hass_areas: dict) -> list[dict]:
    module_areas = []
    for area in hass_areas:
        module_areas.append(
            {
                PROP_AREA_RADIUS: area[CONF_RADIUS],
                PROP_AREA_LAT: area[CONF_LATITUDE],
                PROP_AREA_LONG: area[CONF_LONGITUDE],
            }
        )
    return module_areas


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Create ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.debug("Got request to setup entry.")
    try:
        fuel_prices: FuelPrices = FuelPrices.create(
            enabled_sources=entry.data.get(CONF_SOURCES, None),
            configured_areas=_build_configured_areas(entry.data[CONF_AREAS]),
        )
        await fuel_prices.update()
        hass.data[DOMAIN][entry.entry_id] = FuelPricesCoordinator(
            hass, fuel_prices, entry.entry_id
        )
    except Exception as err:
        _LOGGER.error(err)
        raise CannotConnect from err

    async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
        """Update listener."""
        await hass.config_entries.async_reload(entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_fuel_lookup(call: ServiceCall) -> ServiceResponse:
        """Handle a fuel lookup call."""
        radius = call.data.get("location", {}).get(
            "radius", 8046.72
        )  # this is in meters
        radius = radius / 1609
        lat = call.data.get("location", {}).get("latitude", 0.0)
        long = call.data.get("location", {}).get("longitude", 0.0)
        fuel_type = call.data.get("type")
        return {
            "fuels": await fuel_prices.find_fuel_from_point(
                (lat, long), radius, fuel_type
            )
        }

    async def handle_fuel_location_lookup(call: ServiceCall) -> ServiceResponse:
        """Handle a fuel location lookup call."""
        radius = call.data.get("location", {}).get(
            "radius", 8046.72
        )  # this is in meters
        radius = radius / 1609
        lat = call.data.get("location", {}).get("latitude", 0.0)
        long = call.data.get("location", {}).get("longitude", 0.0)
        locations = await fuel_prices.find_fuel_locations_from_point(
            (lat, long), radius
        )
        locations_built = []
        for loc in locations:
            locations_built.append(loc.__dict__())

        return {"items": locations_built, "sources": entry.data.get("sources", [])}

    hass.services.async_register(
        DOMAIN,
        "find_fuel_station",
        handle_fuel_location_lookup,
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        "find_fuels",
        handle_fuel_lookup,
        supports_response=SupportsResponse.ONLY,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading config entry %s", entry.entry_id)
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
