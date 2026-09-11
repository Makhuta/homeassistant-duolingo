from datetime import timedelta
import logging
from typing import Dict, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
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
        interval = self._clients[0].get_interval() if len(self._clients) > 0 else 30

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self._async_update_data,
            update_interval=timedelta(minutes=interval),
        )
    
    async def _async_update_data(self) -> Dict[str, Any]:
        try:
            data = {}
            errors = []
            for client in self._clients:
                username = client.get_username()
                try:
                    data[username] = await self.hass.async_add_executor_job(client.update)
                except Exception as err:
                    errors.append((username, err))
                    _LOGGER.warning(
                        "Failed to update Duolingo data for %s: %s",
                        username,
                        err,
                        exc_info=True,
                    )

            if errors and not data:
                raise UpdateFailed("Failed to update Duolingo data for all configured users") from errors[0][1]

            return data
        except FailedToLogin as err:
            raise ConfigEntryError("Failed to Log-in") from err
        except UpdateFailed:
            raise
        except Exception as err:
            raise ConfigEntryError("Duolingo encountered unknown error") from err
