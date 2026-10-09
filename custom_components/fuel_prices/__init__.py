"""Fuel Prices integration."""

import copy
import logging

from dataclasses import dataclass

import aiohttp
import voluptuous as vol

from pyfuelprices import FuelPrices
from pyfuelprices.enum import SupportsConfigType
from pyfuelprices.sources import SessionClosedError
from pyfuelprices.sources.mapping import SOURCE_MAP

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import (
    Platform,
    CONF_TIMEOUT,
    CONF_SCAN_INTERVAL,
    CONF_RADIUS,
)
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er, issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import (
    DOMAIN,
    CONF_AREAS,
    CONF_SOURCES,
    METERS_PER_MILE,
    REMOVED_AREA_KEYS,
    REMOVED_ISSUE_IDS,
    REPLACED_SOURCES,
)
from .coordinator import FuelPricesCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]
SERVICES = ["find_fuel_station", "find_fuels", "force_update"]
# No sensible fuel search area is this many miles, so larger values are meters.
LEGACY_RADIUS_METERS_THRESHOLD = 200


@dataclass
class FuelPricesConfig:
    """Represent a Fuel Price Config."""

    coordinator: FuelPricesCoordinator
    areas: list[dict]
    config: ConfigEntry
    session: aiohttp.ClientSession


type FuelPricesConfigEntry = ConfigEntry[FuelPricesConfig]


def _build_module_config(entry: FuelPricesConfigEntry) -> dict:
    """Build a given config entry into the config dict for the pyfuelprices module."""
    sources = entry.options.get(
        CONF_SOURCES, entry.data.get(CONF_SOURCES, {}))
    areas = entry.options.get(CONF_AREAS, entry.data.get(CONF_AREAS, None))
    timeout = entry.options.get(CONF_TIMEOUT, entry.data.get(CONF_TIMEOUT, 30))
    update_interval = entry.options.get(
        CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, 1440)
    )
    return {
        "areas": areas,
        "providers": sources,
        "timeout": timeout,
        "update_interval": update_interval
    }


def _validate_sources(hass: HomeAssistant, sources: dict) -> dict:
    """Return only the sources that exist and have a valid configuration.

    Invalid sources raise a repair issue rather than failing the whole entry.
    """
    valid = {}
    for src, src_config in sources.items():
        if src not in SOURCE_MAP:
            _LOGGER.warning(
                "Source %s is no longer available and will be ignored", src)
            continue
        issue_id = f"source_config_invalid_{src}"
        schema = FuelPrices.get_source_config_schema(src)
        if (
            FuelPrices.source_config_type(src) != SupportsConfigType.NONE
            and schema is not None
        ):
            try:
                schema(src_config or {})
            except vol.Invalid as err:
                _LOGGER.error(
                    "Source %s has an invalid configuration: %s", src, err)
                ir.async_create_issue(
                    hass,
                    domain=DOMAIN,
                    issue_id=issue_id,
                    is_fixable=False,
                    severity=ir.IssueSeverity.ERROR,
                    translation_key="source_config_invalid",
                    translation_placeholders={"source": src},
                )
                continue
        ir.async_delete_issue(hass, DOMAIN, issue_id)
        valid[src] = src_config or {}
    return valid


async def async_setup_entry(hass: HomeAssistant, entry: FuelPricesConfigEntry) -> bool:
    """Create ConfigEntry."""

    default_lat = hass.config.latitude
    default_long = hass.config.longitude
    mod_config = _build_module_config(entry)
    mod_config["providers"] = _validate_sources(hass, mod_config["providers"])
    session = async_create_clientsession(hass)
    try:
        fuel_prices: FuelPrices = FuelPrices.create(
            client_session=session,
            configuration=mod_config
        )
    except Exception as err:
        _LOGGER.error(err)
        await session.close()
        raise CannotConnect from err

    coordinator = FuelPricesCoordinator(
        hass=hass, api=fuel_prices, config_entry=entry)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        await session.close()
        raise

    def _handle_session_closed(err: SessionClosedError) -> HomeAssistantError:
        """Schedule a reload to get a fresh session and return an error to raise."""
        hass.config_entries.async_schedule_reload(entry.entry_id)
        return HomeAssistantError(
            "Fuel prices session was closed, the integration is reloading.")

    async def handle_fuel_lookup(call: ServiceCall) -> ServiceResponse:
        """Handle a fuel lookup call."""
        radius = call.data.get("location", {}).get(
            "radius", 8046.72
        )  # this is in meters
        radius = radius / 1609
        lat = call.data.get("location", {}).get("latitude", default_lat)
        long = call.data.get("location", {}).get("longitude", default_long)
        fuel_type = call.data.get("type")
        source = call.data.get("source", "")
        try:
            return {
                "fuels": await fuel_prices.find_fuel_from_point(
                    (lat, long), radius, fuel_type, source
                )
            }
        except SessionClosedError as err:
            raise _handle_session_closed(err) from err
        except ValueError as err:
            raise HomeAssistantError(
                "Country not available for fuel data.") from err
        except TypeError as err:
            # Raised by pyfuelprices when a station has no price for the fuel.
            raise HomeAssistantError(
                f"Unable to compare fuel prices: {err}") from err

    async def handle_fuel_location_lookup(call: ServiceCall) -> ServiceResponse:
        """Handle a fuel location lookup call."""
        radius = call.data.get("location", {}).get(
            "radius", 8046.72
        )  # this is in meters
        radius = radius / 1609
        lat = call.data.get("location", {}).get("latitude", default_lat)
        long = call.data.get("location", {}).get("longitude", default_long)
        source = call.data.get("source", "")
        try:
            locations = await fuel_prices.find_fuel_locations_from_point(
                (lat, long), radius, source
            )
        except SessionClosedError as err:
            raise _handle_session_closed(err) from err
        except ValueError as err:
            raise HomeAssistantError(
                "Country not available for fuel data.") from err

        return {"items": locations, "sources": entry.data.get("sources", [])}

    async def handle_force_update(call: ServiceCall):
        """Handle a request to force update."""
        try:
            await fuel_prices.update(force=True)
        except SessionClosedError as err:
            raise _handle_session_closed(err) from err

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

    hass.services.async_register(DOMAIN, "force_update", handle_force_update)

    entry.runtime_data = FuelPricesConfig(
        coordinator=coordinator,
        areas=mod_config[CONF_AREAS],
        config=entry,
        session=session,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def update_listener(hass: HomeAssistant, entry: FuelPricesConfigEntry):
        """Update listener."""
        await hass.config_entries.async_reload(entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: FuelPricesConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading config entry %s", entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    await entry.runtime_data.coordinator.api.close()
    await entry.runtime_data.session.close()

    other_loaded = [
        e for e in hass.config_entries.async_entries(DOMAIN)
        if e.entry_id != entry.entry_id and e.state is ConfigEntryState.LOADED
    ]
    if not other_loaded:
        for service in SERVICES:
            hass.services.async_remove(DOMAIN, service)
    return True


def _migrate_to_v5(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Replace removed sources and strip settings for removed features (v4 -> v5)."""
    new_data = copy.deepcopy(dict(config_entry.data))
    new_options = copy.deepcopy(dict(config_entry.options))
    replaced: dict[str, str] = {}
    for store in (new_data, new_options):
        sources = store.get(CONF_SOURCES)
        if isinstance(sources, dict):
            removed = {k: REPLACED_SOURCES[k] for k in sources if k in REPLACED_SOURCES}
            if removed:
                replaced.update(removed)
                sources = {k: v for k, v in sources.items() if k not in removed}
                for replacement in removed.values():
                    sources.setdefault(replacement, {})
                store[CONF_SOURCES] = sources

        for area in store.get(CONF_AREAS) or []:
            for key in REMOVED_AREA_KEYS:
                area.pop(key, None)
            # Areas created from the options flow were saved in meters, not miles.
            if area.get(CONF_RADIUS, 0) > LEGACY_RADIUS_METERS_THRESHOLD:
                area[CONF_RADIUS] = area[CONF_RADIUS] / METERS_PER_MILE

    if replaced:
        _LOGGER.warning(
            "The following fuel price sources have been removed and replaced: %s. "
            "In the UK, the official Government data is available by configuring "
            "the fuelfinder source in the integration options.",
            ", ".join(f"{old} -> {new}" for old, new in sorted(replaced.items())),
        )
        ent_reg = er.async_get(hass)
        prefixes = tuple(f"fuelprices_{src}_" for src in replaced)
        for entity in er.async_entries_for_config_entry(ent_reg, config_entry.entry_id):
            if entity.unique_id.startswith(prefixes):
                ent_reg.async_remove(entity.entity_id)

    for issue_id in REMOVED_ISSUE_IDS:
        ir.async_delete_issue(hass, DOMAIN, issue_id)

    hass.config_entries.async_update_entry(
        config_entry, data=new_data, options=new_options, version=5
    )


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating configuration from version %s",
                  config_entry.version)

    new_data = {**config_entry.data}
    if config_entry.options:
        new_data = {**config_entry.options}

    if config_entry.version > 5:
        # This means the user has downgraded from a future version
        return False

    if config_entry.version == 1:
        hass.config_entries.async_update_entry(
            config_entry, data=new_data, version=2)

    if config_entry.version == 2:
        _LOGGER.warning("Removing morrisons from config entry.")
        if "morrisons" in new_data[CONF_SOURCES]:
            new_data[CONF_SOURCES].remove("morrisons")
        hass.config_entries.async_update_entry(
            config_entry, data=new_data, version=3
        )

    if config_entry.version == 3:
        _LOGGER.warning("Updating configuration for fuel prices.")
        sources = new_data[CONF_SOURCES]
        providers = {}
        for source in sources:
            providers[source] = {}
        new_data[CONF_SOURCES] = providers
        new_data[CONF_SCAN_INTERVAL] = new_data[CONF_SCAN_INTERVAL]/60
        hass.config_entries.async_update_entry(
            config_entry, data=new_data, version=4, options=new_data
        )

    if config_entry.version == 4:
        _migrate_to_v5(hass, config_entry)

    _LOGGER.info("Migration to configuration version %s successful",
                 config_entry.version)

    return True


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
