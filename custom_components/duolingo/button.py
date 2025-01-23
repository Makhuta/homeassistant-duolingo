from typing import Any, Callable, Dict, Optional

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .coordinator import DuolingoDataCoordinator
from .const import (
    DOMAIN,
    CONF_JWT,
    FORCE_SCRAPE,
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Callable,
) -> None:
    """Set up HoneyGain button from config entry."""
    coordinator: DuolingoDataCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([DuolingoForceScan(coordinator, config_entry)], update_before_add=True)


class DuolingoForceScan(ButtonEntity):
    def __init__(self, coordinator: DuolingoDataCoordinator, config_entry: ConfigEntry):
        self._coordinator = coordinator
        self._jwt = config_entry.data[CONF_JWT]

    @property
    def name(self) -> str:
        """Return the name of the entity"""
        return "Duolingo force scrape"
    
    @property
    def icon(self) -> str:
        """Return the icon of the entity"""
        return "mdi:tray-arrow-down"
    
    @property
    def unique_id(self) -> str:
        """Return the unique id of the entity"""
        return f'{self._jwt}_duolingo_force_scrape_button'
    
    async def async_press(self) -> None:
        """Press the button"""
        async_dispatcher_send(self._coordinator.hass, FORCE_SCRAPE)