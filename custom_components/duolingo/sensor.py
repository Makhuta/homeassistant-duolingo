from typing import Any, Dict, Optional
from collections.abc import Callable

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorEntity

from homeassistant.const import (
    CONF_USERNAME, 
    )

from .const import (
    DOMAIN,
    CONF_JWT
)
from .coordinator import DuolingoDataCoordinator
from .helpers import convert_objects

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Callable,
) -> None:
    coordinator: DuolingoDataCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    usernames = config_entry.data[CONF_USERNAME]

    async_add_entities(
        [DuolingoUserInfoSensor(coordinator, config_entry, username, "User") for username in usernames] +
        [DuolingoLanguagesDetailsSensor(coordinator, config_entry, username, "Languages") for username in usernames] +
        [DuolingoLeaderboardSensor(coordinator, config_entry, username, "Leaderboard") for username in usernames] +
        [DuolingoStreakInfoSensor(coordinator, config_entry, username, "Streak") for username in usernames] +
        [DuolingoFriendsSensor(coordinator, config_entry, username, "Friends") for username in usernames]
    )

class DuolingoBaseSensor(CoordinatorEntity[DuolingoDataCoordinator], SensorEntity):
    def __init__(self, coordinator: DuolingoDataCoordinator, config_entry: ConfigEntry, username: str = "", type: str = ""):
        super().__init__(coordinator)
        self._coordinator = {**coordinator.data[username]} if coordinator.data.get(username) else {}
        self._name = f'Duolingo {" " + type.capitalize() if len(type) > 0 else ""}'
        self._username = username
        self._jwt = config_entry.data[CONF_JWT]
        self._type = type
        self.entity_id = f'sensor.{self._username}_{self._name.lower().replace(" ", "_")}'
        self._unit_of_measurement = None
        self._multiple = False

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f'{self._username} {self._type.capitalize()}'

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f'{self._jwt}_Duolingo_{self._username}_{self._type}'

    @property
    def icon(self):
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        if self._unit_of_measurement:
            return self._unit_of_measurement + "s" if self._multiple else ""

    @property
    def device_info(self) -> Dict[str, Any]:
        return {
            "name": self._username,
            "manufacturer": "Duolingo",
            "model": "Scrapper",
            "identifiers": {(DOMAIN, f'{self._jwt}_Duolingo_{self._username}')},
        }

def remove_keys_from_dict(dictionary, keys) -> Dict[str, Any]:
    return {k: (dictionary[k] if dictionary[k] else str(dictionary[k])) for k in set(list(dictionary.keys())) - set(keys)}

class DuolingoUserInfoSensor(DuolingoBaseSensor):
    def __init__(self, coordinator: DuolingoDataCoordinator, config_entry: ConfigEntry, username: str = "", type: str = ""):
        super().__init__(coordinator, config_entry, username, type)
        self._icon = "mdi:account"

    @property
    def state(self) -> Optional[str]:
        """Return the value of the sensor."""
        if "user_info" in self._coordinator:
            if "id" in self._coordinator["user_info"]:
                return self._coordinator["user_info"]["id"]
        return "Unknown"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        if "user_info" in self._coordinator:
            return remove_keys_from_dict(self._coordinator["user_info"], ["language_data"])
        return {}

class DuolingoLanguagesDetailsSensor(DuolingoBaseSensor):
    def __init__(self, coordinator: DuolingoDataCoordinator, config_entry: ConfigEntry, username: str = "", type: str = ""):
        super().__init__(coordinator, config_entry, username, type)
        self._icon = "mdi:flag"

    @property
    def state(self) -> Optional[str]:
        """Return the value of the sensor."""
        if "languages_details" in self._coordinator:
            return len(self._coordinator["languages_details"].keys())
        return 0

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        if "languages_details" in self._coordinator:
            return {value.get("language_string"): value for key, value in self._coordinator["languages_details"].items()}
        return {}

class DuolingoLeaderboardSensor(DuolingoBaseSensor):
    def __init__(self, coordinator: DuolingoDataCoordinator, config_entry: ConfigEntry, username: str = "", type: str = ""):
        super().__init__(coordinator, config_entry, username, type)
        self._icon = "mdi:bulletin-board"
        self._unit_of_measurement = "position"

    @property
    def state(self) -> Optional[str]:
        """Return the value of the sensor."""
        if "leaderboard_position" in self._coordinator:
            self._multiple = self._coordinator["leaderboard_position"] > 1
            return self._coordinator["leaderboard_position"]
        return -1

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        if "leaderboard" in self._coordinator:
            return {(id + 1): self._coordinator["leaderboard"][id] for id in range(len(self._coordinator["leaderboard"]))}
        return {}

class DuolingoStreakInfoSensor(DuolingoBaseSensor):
    def __init__(self, coordinator: DuolingoDataCoordinator, config_entry: ConfigEntry, username: str = "", type: str = ""):
        super().__init__(coordinator, config_entry, username, type)
        self._icon = "mdi:fire"
        self._unit_of_measurement = "day"

    @property
    def state(self) -> Optional[str]:
        """Return the value of the sensor."""
        if "streak_info" in self._coordinator:
            if "length" in self._coordinator["streak_info"]:
                self._multiple = self._coordinator["streak_info"]["length"] > 1
                return self._coordinator["streak_info"]["length"]
        return -1

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        if "streak_info" in self._coordinator:
            return convert_objects(self._coordinator["streak_info"])
        return {}

class DuolingoFriendsSensor(DuolingoBaseSensor):
    def __init__(self, coordinator: DuolingoDataCoordinator, config_entry: ConfigEntry, username: str = "", type: str = ""):
        super().__init__(coordinator, config_entry, username, type)
        self._icon = "mdi:account"

    @property
    def state(self) -> Optional[str]:
        """Return the value of the sensor."""
        if "friends" in self._coordinator:
                return len(self._coordinator["friends"])
        return 0

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        if "friends" in self._coordinator:
            return {(friend.get("displayName", friend.get("username"))): friend for friend in self._coordinator["friends"]}
        return {}