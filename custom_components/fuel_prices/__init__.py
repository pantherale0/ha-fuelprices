"""Fuel Prices integration."""

import logging

from pyfuelprices import FuelPrices

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .coordinator import FuelPricesCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.DEVICE_TRACKER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Create ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.debug("Got request to setup entry.")
    try:
        fuel_prices: FuelPrices = FuelPrices.create(
            enabled_sources=entry.data.get("sources", None)
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

    def handle_fuel_lookup(call: ServiceCall) -> ServiceResponse:
        """Handle a fuel lookup call."""
        radius = call.data.get("location", {}).get(
            "radius", 8046.72
        )  # this is in meters
        radius = radius / 1609
        lat = call.data.get("location", {}).get("latitude", 0.0)
        long = call.data.get("location", {}).get("longitude", 0.0)
        fuel_type = call.data.get("type")
        return {
            "fuels": fuel_prices.find_fuel_from_point((lat, long), radius, fuel_type)
        }

    def handle_fuel_location_lookup(call: ServiceCall) -> ServiceResponse:
        """Handle a fuel location lookup call."""
        radius = call.data.get("location", {}).get(
            "radius", 8046.72
        )  # this is in meters
        radius = radius / 1609
        lat = call.data.get("location", {}).get("latitude", 0.0)
        long = call.data.get("location", {}).get("longitude", 0.0)
        location_ids = fuel_prices.find_fuel_locations_from_point((lat, long), radius)
        locations = []
        for loc_id in location_ids:
            loc = fuel_prices.get_fuel_location(loc_id)
            built = {
                "name": loc.name,
                "last_update": loc.last_updated,
                "address": loc.address,
                "latitude": loc.lat,
                "longitude": loc.long,
                "brand": loc.brand,
            }
            for fuel in loc.available_fuels:
                built[fuel.fuel_type] = fuel.cost
            locations.append(built)

        return {"items": locations, "sources": entry.data.get("sources", [])}

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
