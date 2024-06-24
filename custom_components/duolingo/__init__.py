from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import (
    CONF_USERNAME, 
    )

from .const import (
    DOMAIN,
    CONF_JWT
    )
from .coordinator import DuolingoDataCoordinator
from .helpers import setup_client
from .duolingo_api import (
    FailedToLogin
)

PLATFORMS = [
    Platform.SENSOR
]

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    try:
        clients = await hass.async_add_executor_job(
            setup_client,
            config_entry.data[CONF_USERNAME],
            config_entry.data[CONF_JWT],
        )
    except FailedToLogin as err:
        raise ConfigEntryNotReady("Failed to Log-in") from err
    coordinator = DuolingoDataCoordinator(hass, clients)

    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))

    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload Duolingo config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    ):
        del hass.data[DOMAIN][config_entry.entry_id]
        if not hass.data[DOMAIN]:
            del hass.data[DOMAIN]
    return unload_ok

async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)