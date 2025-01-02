from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import (
    CONF_USERNAME, 
    )
from homeassistant.helpers.device_registry import DeviceEntry, async_get as async_get_device_registry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.components.persistent_notification import (
    async_create as async_create_persistent_notification,
)

from .const import (
    DOMAIN,
    CONF_JWT,
    CONF_INTERVAL
    )
from .coordinator import DuolingoDataCoordinator
from .helpers import setup_client
from .duolingo_api import (
    FailedToLogin
)

PLATFORMS = [
    Platform.SENSOR,
]

async def cleanup_existing_entities_and_devices(hass: HomeAssistant, config_entry: ConfigEntry):
    entity_registry = async_get_entity_registry(hass)
    device_registry = async_get_device_registry(hass)

    for entity_id, entity in list(entity_registry.entities.items()):
        if entity.config_entry_id == config_entry.entry_id:
            entity_registry.async_remove(entity_id)

    for device_id, device in list(device_registry.devices.items()):
        if config_entry.entry_id in device.config_entries:
            device_registry.async_remove_device(device_id)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    try:
        clients = await hass.async_add_executor_job(
            setup_client,
            config_entry.data[CONF_USERNAME],
            config_entry.data[CONF_JWT],
            config_entry.data.get(CONF_INTERVAL, 30),
        )
    except FailedToLogin as err:
        raise ConfigEntryNotReady("Failed to Log-in") from err
    coordinator = DuolingoDataCoordinator(hass, clients)

    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = coordinator

    await cleanup_existing_entities_and_devices(hass, config_entry)

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

async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove config entry from a device."""
    if device_entry is not None:
        async_create_persistent_notification(
            hass,
            title="Device removal",
            message=f"Device was removed from system.",
        )
        return True
    
    return False