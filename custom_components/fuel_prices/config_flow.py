"""Config flow for Fuel Prices."""

import logging
from typing import Any
from homeassistant.config_entries import ConfigEntry, OptionsFlow

from pyfuelprices.sources.mapping import SOURCE_MAP, COUNTRY_MAP
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector
from homeassistant.helpers import config_validation as cv
from homeassistant.core import callback
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
    CONF_NAME,
    CONF_TIMEOUT,
    CONF_SCAN_INTERVAL,
)

from .const import DOMAIN, NAME, CONF_AREAS, CONF_SOURCES, CONF_STATE_VALUE, CONF_CHEAPEST_SENSORS, CONF_CHEAPEST_SENSORS_COUNT, CONF_CHEAPEST_SENSORS_FUEL_TYPE

_LOGGER = logging.getLogger(__name__)

AREA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): selector.TextSelector(),
        vol.Required(CONF_RADIUS, default=5.0): selector.NumberSelector(
            selector.NumberSelectorConfig(
                mode=selector.NumberSelectorMode.BOX,
                unit_of_measurement="miles",
                min=1,
                max=50,
                step=0.1,
            )
        ),
        vol.Inclusive(
            CONF_LATITUDE, "coordinates", "Latitude and longitude must exist together"
        ): cv.latitude,
        vol.Inclusive(
            CONF_LONGITUDE, "coordinates", "Latitude and longitude must exist together"
        ): cv.longitude,
        vol.Optional(CONF_CHEAPEST_SENSORS, default=False): selector.BooleanSelector(),
        vol.Optional(CONF_CHEAPEST_SENSORS_COUNT, default=5): selector.NumberSelector(
            selector.NumberSelectorConfig(
                mode=selector.NumberSelectorMode.SLIDER,
                min=1,
                max=10,
                step=1
            )
        ),
        vol.Optional(CONF_CHEAPEST_SENSORS_FUEL_TYPE, default=""): selector.TextSelector(),
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 2
    configured_areas: list[dict] = []
    configured_sources = []
    configuring_area = {}
    configuring_index = -1
    state_value = "name"
    timeout = None
    interval = None

    @property
    def configured_area_names(self) -> list[str]:
        """Return a list of area names."""
        items = []
        for area in self.configured_areas:
            items.append(area["name"])
        return items

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the intial step."""
        # only one config entry allowed
        # users should use the options flow to adjust areas and sources.
        await self.async_set_unique_id(NAME)
        self._abort_if_unique_id_configured()
        self.configured_areas = []
        self.configured_sources = []
        self.configuring_area = {}
        self.configuring_index = -1
        self.timeout = 10
        self.interval = 1440
        # add the home location as a default (this can optionally be removed).
        self.configured_areas.append(
            {
                CONF_NAME: self.hass.config.location_name,
                CONF_LATITUDE: self.hass.config.latitude,
                CONF_LONGITUDE: self.hass.config.longitude,
                CONF_RADIUS: 10.0,
            }
        )
        return await self.async_step_main_menu()

    async def async_step_main_menu(self, _: None = None):
        """Display configuration menu."""
        return self.async_show_menu(
            step_id="main_menu",
            menu_options={
                "area_menu": "Configure areas to create devices/sensors",
                "sources": "Configure data collector sources",
                "finished": "Complete setup",
            },
        )

    async def async_step_sources(self, user_input: dict[str, Any] | None = None):
        """Set data source config."""
        if user_input is not None:
            self.configured_sources = user_input[CONF_SOURCES]
            self.timeout = user_input[CONF_TIMEOUT]
            self.interval = user_input[CONF_SCAN_INTERVAL]
            return await self.async_step_main_menu(None)
        return self.async_show_form(
            step_id="sources",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SOURCES, default=self.configured_sources
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            mode=selector.SelectSelectorMode.DROPDOWN,
                            options=list(SOURCE_MAP),
                            multiple=True,
                        )
                    ),
                    vol.Optional(
                        CONF_TIMEOUT,
                        default=self.timeout,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=5,
                            max=60,
                            unit_of_measurement="s",
                        )
                    ),
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.interval,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=1,
                            max=1440,
                            unit_of_measurement="m",
                        )
                    )
                }
            ),
        )

    async def async_step_area_menu(self, _: None = None) -> FlowResult:
        """Show the area menu."""
        return self.async_show_menu(
            step_id="area_menu",
            menu_options={
                "area_create": "Define a new area",
                "area_update_select": "Update an area",
                "area_delete": "Delete an area",
                "main_menu": "Return to main menu",
            },
        )

    async def async_step_area_create(self, user_input: dict[str, Any] | None = None):
        """Handle an area configuration."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self.configured_areas.append(
                {
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_LATITUDE: user_input[CONF_LATITUDE],
                    CONF_LONGITUDE: user_input[CONF_LONGITUDE],
                    CONF_RADIUS: user_input[CONF_RADIUS],
                    CONF_CHEAPEST_SENSORS: user_input[CONF_CHEAPEST_SENSORS],
                    CONF_CHEAPEST_SENSORS_COUNT: user_input[CONF_CHEAPEST_SENSORS_COUNT],
                    CONF_CHEAPEST_SENSORS_FUEL_TYPE: user_input[CONF_CHEAPEST_SENSORS_FUEL_TYPE]
                }
            )
            return await self.async_step_area_menu()
        return self.async_show_form(
            step_id="area_create", data_schema=AREA_SCHEMA, errors=errors
        )

    async def async_step_area_update_select(
        self, user_input: dict[str, Any] | None = None
    ):
        """Show a menu to allow the user to select what option to update."""
        if user_input is not None:
            for i, data in enumerate(self.configured_areas):
                if self.configured_areas[i]["name"] == user_input[CONF_NAME]:
                    self.configuring_area = data
                    self.configuring_index = i
                    break
            return await self.async_step_area_update()
        if len(self.configured_areas) > 0:
            return self.async_show_form(
                step_id="area_update_select",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_NAME): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                mode=selector.SelectSelectorMode.LIST,
                                options=self.configured_area_names,
                            )
                        )
                    }
                ),
            )
        return await self.async_step_area_menu()

    async def async_step_area_update(self, user_input: dict[str, Any] | None = None):
        """Handle an area update."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self.configured_areas.pop(self.configuring_index)
            self.configured_areas.append(
                {
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_LATITUDE: user_input[CONF_LATITUDE],
                    CONF_LONGITUDE: user_input[CONF_LONGITUDE],
                    CONF_RADIUS: user_input[CONF_RADIUS],
                    CONF_CHEAPEST_SENSORS: user_input[CONF_CHEAPEST_SENSORS],
                    CONF_CHEAPEST_SENSORS_COUNT: user_input[CONF_CHEAPEST_SENSORS_COUNT],
                    CONF_CHEAPEST_SENSORS_FUEL_TYPE: user_input[CONF_CHEAPEST_SENSORS_FUEL_TYPE]
                }
            )
            return await self.async_step_area_menu()
        return self.async_show_form(
            step_id="area_update",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME, default=self.configuring_area[CONF_NAME]
                    ): selector.TextSelector(),
                    vol.Required(
                        CONF_RADIUS, default=self.configuring_area[CONF_RADIUS]
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="miles",
                            min=1,
                            max=50,
                            step=0.1,
                        )
                    ),
                    vol.Inclusive(
                        CONF_LATITUDE,
                        "coordinates",
                        "Latitude and longitude must exist together",
                        default=self.configuring_area[CONF_LATITUDE],
                    ): cv.latitude,
                    vol.Inclusive(
                        CONF_LONGITUDE,
                        "coordinates",
                        "Latitude and longitude must exist together",
                        default=self.configuring_area[CONF_LONGITUDE],
                    ): cv.longitude,
                    vol.Optional(
                        CONF_CHEAPEST_SENSORS,
                        default=self.configuring_area[CONF_CHEAPEST_SENSORS]
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_CHEAPEST_SENSORS_COUNT,
                        default=self.configuring_area[CONF_CHEAPEST_SENSORS_COUNT]
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.SLIDER,
                            min=1,
                            max=10,
                            step=1
                        )
                    ),
                    vol.Optional(
                        CONF_CHEAPEST_SENSORS_FUEL_TYPE,
                        default=self.configuring_area[CONF_CHEAPEST_SENSORS_FUEL_TYPE]
                    ): selector.TextSelector()
                }
            ),
            errors=errors,
        )

    async def async_step_area_delete(self, user_input: dict[str, Any] | None = None):
        """Delete a configured area."""
        if user_input is not None:
            for i, data in enumerate(self.configured_areas):
                if data["name"] == user_input[CONF_NAME]:
                    self.configured_areas.pop(i)
                    break
            return await self.async_step_area_menu()
        if len(self.configured_areas) > 0:
            return self.async_show_form(
                step_id="area_delete",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_NAME): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                mode=selector.SelectSelectorMode.LIST,
                                options=self.configured_area_names,
                            )
                        )
                    }
                ),
            )
        return await self.async_step_area_menu()

    async def async_step_finished(self, user_input: dict[str, Any] | None = None):
        """Save configuration."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if len(self.configured_sources) > 0:
                user_input[CONF_SOURCES] = self.configured_sources
            elif self.hass.config.country is not None:
                user_input[CONF_SOURCES] = COUNTRY_MAP.get(
                    self.hass.config.country)
            else:
                user_input[CONF_SOURCES] = list(SOURCE_MAP)
            user_input[CONF_AREAS] = self.configured_areas
            user_input[CONF_SCAN_INTERVAL] = self.interval
            user_input[CONF_TIMEOUT] = self.timeout
            user_input[CONF_STATE_VALUE] = self.state_value
            return self.async_create_entry(title=NAME, data=user_input)
        return self.async_show_form(step_id="finished", errors=errors, last_step=True)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return option flow."""
        return FuelPricesOptionsFlow(config_entry)


class FuelPricesOptionsFlow(config_entries.OptionsFlow):
    """OptionsFlow for fuel_prices module."""

    configured_areas: list[dict] = []
    configured_sources = []
    configuring_area = {}
    configuring_index = -1
    timeout = 10
    interval = 1440
    state_value = "name"

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.configured_areas = config_entry.options.get(
            CONF_AREAS, config_entry.data.get(CONF_AREAS, [])
        )
        self.configured_sources = config_entry.options.get(
            CONF_SOURCES, config_entry.data.get(CONF_SOURCES, [])
        )
        self.timeout = config_entry.options.get(
            CONF_TIMEOUT, config_entry.data.get(CONF_TIMEOUT, 10)
        )
        self.interval = config_entry.options.get(
            CONF_SCAN_INTERVAL, config_entry.data.get(CONF_SCAN_INTERVAL, 1440)
        )
        self.state_value = config_entry.options.get(
            CONF_STATE_VALUE, config_entry.data.get(CONF_STATE_VALUE, "name")
        )

    @property
    def configured_area_names(self) -> list[str]:
        """Return a list of area names."""
        items = []
        for area in self.configured_areas:
            items.append(area["name"])
        return items

    async def _async_create_entry(self) -> config_entries.FlowResult:
        """Create an entry."""
        return self.async_create_entry(
            title=self.config_entry.title,
            data={
                CONF_AREAS: self.configured_areas,
                CONF_SOURCES: self.configured_sources,
                CONF_SCAN_INTERVAL: self.interval,
                CONF_TIMEOUT: self.timeout,
                CONF_STATE_VALUE: self.state_value
            }
        )

    async def async_step_init(self, _: None = None):
        """User init option flow."""
        return await self.async_step_main_menu()

    async def async_step_main_menu(self, _: None = None):
        """Display configuration menu."""
        return self.async_show_menu(
            step_id="main_menu",
            menu_options={
                "area_menu": "Configure areas to create devices/sensors",
                "sources": "Configure data collector sources",
                "finished": "Complete re-configuration",
            },
        )

    async def async_step_sources(self, user_input: dict[str, Any] | None = None):
        """Set data source config."""
        if user_input is not None:
            self.configured_sources = user_input[CONF_SOURCES]
            self.timeout = user_input[CONF_TIMEOUT]
            self.interval = user_input[CONF_SCAN_INTERVAL]
            self.state_value = user_input[CONF_STATE_VALUE]
            return await self.async_step_main_menu(None)
        return self.async_show_form(
            step_id="sources",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SOURCES, default=self.configured_sources
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            mode=selector.SelectSelectorMode.DROPDOWN,
                            options=list(SOURCE_MAP),
                            multiple=True,
                        )
                    ),
                    vol.Optional(
                        CONF_TIMEOUT,
                        default=self.timeout,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=5,
                            max=60,
                            unit_of_measurement="s",
                        )
                    ),
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.interval,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            min=1,
                            max=1440,
                            unit_of_measurement="m",
                        )
                    ),
                    vol.Optional(
                        CONF_STATE_VALUE,
                        default=self.state_value
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            multiline=False,
                            type=selector.TextSelectorType.TEXT
                        )
                    )
                }
            ),
        )

    async def async_step_area_menu(self, _: None = None) -> FlowResult:
        """Show the area menu."""
        return self.async_show_menu(
            step_id="area_menu",
            menu_options={
                "area_create": "Define a new area",
                "area_update_select": "Update an area",
                "area_delete": "Delete an area",
                "main_menu": "Return to main menu",
            },
        )

    async def async_step_area_create(self, user_input: dict[str, Any] | None = None):
        """Handle an area configuration."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self.configured_areas.append(
                {
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_LATITUDE: user_input[CONF_LATITUDE],
                    CONF_LONGITUDE: user_input[CONF_LONGITUDE],
                    CONF_RADIUS: user_input[CONF_RADIUS],
                    CONF_CHEAPEST_SENSORS: user_input[CONF_CHEAPEST_SENSORS],
                    CONF_CHEAPEST_SENSORS_COUNT: user_input[CONF_CHEAPEST_SENSORS_COUNT],
                    CONF_CHEAPEST_SENSORS_FUEL_TYPE: user_input[CONF_CHEAPEST_SENSORS_FUEL_TYPE]
                }
            )
            return await self.async_step_area_menu()
        return self.async_show_form(
            step_id="area_create", data_schema=AREA_SCHEMA, errors=errors
        )

    async def async_step_area_update_select(
        self, user_input: dict[str, Any] | None = None
    ):
        """Show a menu to allow the user to select what option to update."""
        if user_input is not None:
            for i, data in enumerate(self.configured_areas):
                if self.configured_areas[i]["name"] == user_input[CONF_NAME]:
                    self.configuring_area = data
                    self.configuring_index = i
                    break
            return await self.async_step_area_update()
        if len(self.configured_areas) > 0:
            return self.async_show_form(
                step_id="area_update_select",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_NAME): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                mode=selector.SelectSelectorMode.LIST,
                                options=self.configured_area_names,
                            )
                        )
                    }
                ),
            )
        return await self.async_step_area_menu()

    async def async_step_area_update(self, user_input: dict[str, Any] | None = None):
        """Handle an area update."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self.configured_areas.pop(self.configuring_index)
            self.configured_areas.append(
                {
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_LATITUDE: user_input[CONF_LATITUDE],
                    CONF_LONGITUDE: user_input[CONF_LONGITUDE],
                    CONF_RADIUS: user_input[CONF_RADIUS],
                    CONF_CHEAPEST_SENSORS: user_input[CONF_CHEAPEST_SENSORS],
                    CONF_CHEAPEST_SENSORS_COUNT: user_input[CONF_CHEAPEST_SENSORS_COUNT],
                    CONF_CHEAPEST_SENSORS_FUEL_TYPE: user_input[CONF_CHEAPEST_SENSORS_FUEL_TYPE]
                }
            )
            return await self.async_step_area_menu()
        return self.async_show_form(
            step_id="area_update",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME, default=self.configuring_area[CONF_NAME]
                    ): selector.TextSelector(),
                    vol.Required(
                        CONF_RADIUS, default=self.configuring_area[CONF_RADIUS]
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="miles",
                            min=1,
                            max=50,
                            step=0.1,
                        )
                    ),
                    vol.Inclusive(
                        CONF_LATITUDE,
                        "coordinates",
                        "Latitude and longitude must exist together",
                        default=self.configuring_area[CONF_LATITUDE],
                    ): cv.latitude,
                    vol.Inclusive(
                        CONF_LONGITUDE,
                        "coordinates",
                        "Latitude and longitude must exist together",
                        default=self.configuring_area[CONF_LONGITUDE],
                    ): cv.longitude,
                    vol.Optional(
                        CONF_CHEAPEST_SENSORS,
                        default=self.configuring_area[CONF_CHEAPEST_SENSORS]
                    ): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_CHEAPEST_SENSORS_COUNT,
                        default=self.configuring_area[CONF_CHEAPEST_SENSORS_COUNT]
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            mode=selector.NumberSelectorMode.SLIDER,
                            min=1,
                            max=10,
                            step=1
                        )
                    ),
                    vol.Optional(
                        CONF_CHEAPEST_SENSORS_FUEL_TYPE,
                        default=self.configuring_area[CONF_CHEAPEST_SENSORS_FUEL_TYPE]
                    ): selector.TextSelector()
                }
            ),
            errors=errors,
        )

    async def async_step_area_delete(self, user_input: dict[str, Any] | None = None):
        """Delete a configured area."""
        if user_input is not None:
            for i, data in enumerate(self.configured_areas):
                if data["name"] == user_input[CONF_NAME]:
                    self.configured_areas.pop(i)
                    break
            return await self.async_step_area_menu()
        if len(self.configured_areas) > 0:
            return self.async_show_form(
                step_id="area_delete",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_NAME): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                mode=selector.SelectSelectorMode.LIST,
                                options=self.configured_area_names,
                            )
                        )
                    }
                ),
            )
        return await self.async_step_area_menu()

    async def async_step_finished(self, user_input: dict[str, Any] | None = None):
        """Save configuration."""
        errors: dict[str, str] = {}
        if user_input is not None:
            return await self._async_create_entry()
        return self.async_show_form(step_id="finished", errors=errors, last_step=True)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
