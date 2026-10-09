"""Fuel Prices data hub."""

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from pyfuelprices import FuelPrices, UpdateExceptionGroup
from pyfuelprices.sources import SessionClosedError, UpdateFailedError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)


class FuelPricesCoordinator(DataUpdateCoordinator):
    """Fuel Prices data coordinator."""

    def __init__(self, hass: HomeAssistant, api: FuelPrices, config_entry: ConfigEntry) -> None:
        """Init the coordinator."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=config_entry.entry_id,
            config_entry=config_entry,
            update_interval=timedelta(minutes=30),
        )
        self.api: FuelPrices = api

    def _session_closed(self) -> UpdateFailed:
        """Schedule a reload so the entry gets a fresh client session."""
        _LOGGER.warning(
            "Client session closed unexpectedly, reloading fuel prices")
        self.hass.config_entries.async_schedule_reload(
            self.config_entry.entry_id)
        return UpdateFailed("Client session closed, reloading integration")

    async def _async_update_data(self):
        """Fetch and update data from the API."""
        try:
            async with asyncio.timeout(240):
                return await self.api.update()
        except SessionClosedError as err:
            raise self._session_closed() from err
        except TimeoutError as err:
            _LOGGER.exception(
                "Timeout updating fuel price data, will retry later: %s", err)
        except TypeError as err:
            _LOGGER.exception(
                "Error updating fuel price data, will retry later: %s", err)
        except UpdateFailedError as err:
            _LOGGER.exception(
                "Error communicating with a service %s", err.status, exc_info=err)
        except UpdateExceptionGroup as err:
            if err.session_closed:
                raise self._session_closed() from err
            for e, v in err.failed_providers.items():
                _LOGGER.exception(
                    "Error communicating with service %s - %s", e, v, exc_info=v
                )
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API {err}") from err
