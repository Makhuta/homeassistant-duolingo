from datetime import timedelta
import logging
from typing import Dict, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError

from .const import DOMAIN
from .duolingo_api import (
    DuolingoAPI,
    FailedToLogin,
)

_LOGGER = logging.getLogger(__name__)

class DuolingoDataCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, clients: list[DuolingoAPI]):
        self._clients = clients

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self._async_update_data,
            update_interval=timedelta(minutes=30),
        )
    
    async def _async_update_data(self) -> Dict[str, Any]:
        try:
            data = {}
            for client in self._clients:
                try:
                    data[client.get_username()] = await self.hass.async_add_executor_job(client.update)
                except:
                    pass
            return data
        except FailedToLogin as err:
            raise ConfigEntryError("Failed to Log-in") from err
        except Exception as err:
            raise ConfigEntryError("Duolingo encoutered unknown") from err