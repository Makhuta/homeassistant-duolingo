from typing import Any, Dict, Optional, Final
from collections.abc import Callable

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorEntity, SensorStateClass

from homeassistant.const import (
    CONF_USERNAME,
    EntityCategory
    )

from .const import (
    DOMAIN,
    CONF_JWT,
    functionType
)
from .coordinator import DuolingoDataCoordinator
from .helpers import convert_objects, camel_to_snake
from .entity import DuolingoSensor, DuolingoEntityDescription

import logging
_LOGGER = logging.getLogger(__name__)

SENSORS: list[DuolingoEntityDescription | Callable] = [
    DuolingoEntityDescription(
        key="user_info",
        name="User",
        state="total_xp",
        attrs=[
            {"key": "id", "name": "id", "value": lambda x: str(x)},
            {"key": "learning_language_string", "name": "learning_language", "value": lambda x: str(x)},
            {"key": "username", "name": "username", "value": lambda x: str(x)},
            {"key": "fullname", "name": "fullname", "value": lambda x: str(x)},
            {"key": "total_xp", "name": "total_xp", "value": lambda x: int(x)},
            {"key": "gems", "name": "gems", "value": lambda x: int(x)},
            {"key": "languages", "name": "languages", "value": lambda x: list(x)},
            ],
        icon="mdi:account",
        entity_category=EntityCategory.DIAGNOSTIC,
        unit="XP"
    ),
    DuolingoEntityDescription(
        key="leaderboard",
        name="Leaderboard",
        state="position",
        attrs=lambda x: {(id + 1): {camel_to_snake(key): value for key, value in x.get("board")[id].items() if key in ["display_name", "has_plus", "has_recent_activity_15", "score", "streak_extended_today", "user_id"]} for id in range(len(x.get("board")))},
        icon="mdi:bulletin-board",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DuolingoEntityDescription(
        key="friends",
        name="Friends",
        state=lambda x: len(x),
        attrs=lambda x: {friend.get("displayName", friend.get("username")): {camel_to_snake(key): value for key, value in friend.items() if key in ["displayName", "hasSubscription", "isCurrentlyActive", "totalXp", "userId", "username"]} for friend in x},
        icon="mdi:bulletin-board",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DuolingoEntityDescription(
        key="streak_info",
        name="Streak",
        state="length",
        attrs=lambda x: {**{camel_to_snake(key): value for key, value in x.items() if key in ["daily_goal", "length", "streak_extended_today", "xpGoal"]}, **{camel_to_snake(key): x.get(f'currentStreak.{key}') for key in ["endDate", "lastExtendedDate", "startDate"] if x.get(f'currentStreak.{key}')}},
        icon=("mdi:fire", "mdi:fire-off"),
        icon_switch="streak_extended_today",
        entity_category=EntityCategory.DIAGNOSTIC,
        unit="day",
    ),
    DuolingoEntityDescription(
        key="streak_info",
        name="Longest Streak",
        state=lambda x: x.get("longestStreak.length"),
        attrs=lambda x: {camel_to_snake(key): x.get(f'longestStreak.{key}') for key in ["endDate", "achieveDate" ,"startDate"] if x.get(f'longestStreak.{key}')},
        icon="mdi:fire-off",
        entity_category=EntityCategory.DIAGNOSTIC,
        unit="day",
    ),
    DuolingoEntityDescription(
        key="streak_info",
        name="Last Streak",
        state=lambda x: x.get("previousStreak.length"),
        attrs=lambda x: {camel_to_snake(key): x.get(f'previousStreak.{key}') for key in ["endDate","lastExtendedDate" ,"startDate"] if x.get(f'previousStreak.{key}')},
        icon="mdi:fire-off",
        entity_category=EntityCategory.DIAGNOSTIC,
        unit="day",
    ),
    lambda userCoordinator: generate_languages(userCoordinator)
]

def generate_languages(userCoordinator) -> list[DuolingoEntityDescription]:
    languages_details = userCoordinator.get("languages_details", {})
    generated = []
    for key, value in languages_details.items():
        if key.endswith("language"):
            langKey = value
            langString = languages_details.get(f'{langKey}.language_string', langKey)

            generated.append(
                DuolingoEntityDescription(
                    key="languages_details",
                    name=f'Language {langString.capitalize()}',
                    state=f'{langKey}.points',
                    attrs=(lambda lang: (lambda x: {k: x.get(f'{lang}.{k}') for k in ["language_string", "points", "language", "level", "current_learning"] if x.get(f'{lang}.{k}')}))(langKey),
                    icon="mdi:flag",
                    unit="XP",
                    entity_category=EntityCategory.DIAGNOSTIC
                )
            )

    return generated

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Callable,
) -> None:
    coordinator: DuolingoDataCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    usernames = config_entry.data[CONF_USERNAME]
    jwt = config_entry.data[CONF_JWT]

    sensor_per_username = []
    for username in usernames:
        for sensor in SENSORS:
            if type(sensor) == functionType:
                userCoordinator = {**coordinator.data[username]} if coordinator.data.get(username) else {}
                for generatedSensor in sensor(userCoordinator):
                    sensor_per_username.append(DuolingoSensor(coordinator, jwt, username, generatedSensor))
            else:
                sensor_per_username.append(DuolingoSensor(coordinator, jwt, username, sensor))

    async_add_entities(
        sensor_per_username
    )

