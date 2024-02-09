"""Fuel Prices integration."""

import contextlib
import logging

from datetime import timedelta

from pyfuelprices import FuelPrices
from pyfuelprices.const import PROP_AREA_LAT, PROP_AREA_LONG, PROP_AREA_RADIUS

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    Platform,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
    CONF_TIMEOUT,
    CONF_SCAN_INTERVAL,
)
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
    _LOGGER.debug("Got request to setup entry.")
    sources = entry.options.get(CONF_SOURCES, entry.data.get(CONF_SOURCES, None))
    areas = entry.options.get(CONF_AREAS, entry.data.get(CONF_AREAS, None))
    timeout = entry.options.get(CONF_TIMEOUT, entry.data.get(CONF_TIMEOUT, 30))
    update_interval = entry.options.get(
        CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, 1440)
    )
    default_lat = hass.config.latitude
    default_long = hass.config.longitude
    try:
        fuel_prices: FuelPrices = FuelPrices.create(
            enabled_sources=sources,
            configured_areas=_build_configured_areas(areas),
            timeout=timedelta(seconds=timeout),
            update_interval=timedelta(minutes=update_interval),
        )
        with contextlib.suppress(TimeoutError):
            await fuel_prices.update()
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = FuelPricesCoordinator(
            hass, fuel_prices, entry.entry_id
        )
    except Exception as err:
        _LOGGER.error(err)
        raise CannotConnect from err

    async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
        """Update listener."""
        await hass.data[DOMAIN][entry.entry_id].api.client_session.close()
        await hass.config_entries.async_reload(entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_fuel_lookup(call: ServiceCall) -> ServiceResponse:
        """Handle a fuel lookup call."""
        radius = call.data.get("location", {}).get(
            "radius", 8046.72
        )  # this is in meters
        radius = radius / 1609
        lat = call.data.get("location", {}).get("latitude", default_lat)
        long = call.data.get("location", {}).get("longitude", default_long)
        fuel_type = call.data.get("type")
        try:
            return {
                "fuels": await fuel_prices.find_fuel_from_point(
                    (lat, long), radius, fuel_type
                )
            }
        except ValueError as err:
            raise HomeAssistantError("Country not available for fuel data.") from err

    async def handle_fuel_location_lookup(call: ServiceCall) -> ServiceResponse:
        """Handle a fuel location lookup call."""
        radius = call.data.get("location", {}).get(
            "radius", 8046.72
        )  # this is in meters
        radius = radius / 1609
        lat = call.data.get("location", {}).get("latitude", default_lat)
        long = call.data.get("location", {}).get("longitude", default_long)
        try:
            locations = await fuel_prices.find_fuel_locations_from_point(
                (lat, long), radius
            )
        except ValueError as err:
            raise HomeAssistantError("Country not available for fuel data.") from err

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
        await hass.data[DOMAIN][entry.entry_id].api.client_session.close()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
