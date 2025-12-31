from typing import Any, Dict, Optional, Final
from collections.abc import Callable
from datetime import datetime, timedelta

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
    functionType,
)
from .coordinator import DuolingoDataCoordinator
from .helpers import convert_objects, camel_to_snake
from .entity import DuolingoSensor, DuolingoLeaderboardSensor, DuolingoEntityDescription

import logging
_LOGGER = logging.getLogger(__name__)

def add_weekly_xp(x):
    today = datetime.today()
    out = {}
    for day_of_week in range(today.weekday() + 1):
        new_date = today - timedelta(days=day_of_week)
        date_key = "%02d.%02d.%04d" % (new_date.day, new_date.month, new_date.year)
        if date_key in x:
            out[date_key] = x[date_key]
    
    return out

def get_prefix(d, p):
    p = p + "."
    out = {key.removeprefix(p): value for key, value in d.items() if key.startswith(p)}
    return out

def get_by_item(l, key, value, default=None):
    for item in l:
        if item[key] == value:
            return item
    return default

SENSORS: list[DuolingoEntityDescription | Callable] = [
    DuolingoEntityDescription(
        key="user_data",
        name="User",
        state="total_xp",
        attrs=[
            {"key": "user_id", "name": "id", "value": lambda x: str(x)},
            {"key": "learning_language", "name": "learning_language", "value": lambda x: str(x)},
            {"key": "uzername", "name": "username", "value": lambda x: str(x)},
            {"key": "fullname", "name": "fullname", "value": lambda x: str(x)},
            {"key": "total_xp", "name": "total_xp", "value": lambda x: int(x)},
            {"key": "gems", "name": "gems", "value": lambda x: int(x) if int(x) > 0 else None},
            {"key": "languages", "name": "languages", "value": lambda x: list(x)},
            {"key": "avatar", "name": "avatar", "value": lambda x: str(x)},
            ],
        icon="mdi:account",
        entity_category=EntityCategory.DIAGNOSTIC,
        unit="XP"
    ),
    DuolingoEntityDescription(
        key="user_data",
        name="Gems",
        state=lambda x: int(x.get("gems")) if int(x.get("gems")) > 0 else None,
        icon="mdi:diamond",
        entity_category=EntityCategory.DIAGNOSTIC,
        unit="Gems"
    ),
    DuolingoEntityDescription(
        key="leaderboard_data",
        name="Leaderboard",
        state=lambda x: int(x.get("position")) if int(x.get("position")) > 0 else None,
        attrs="ranking",
        icon="mdi:bulletin-board",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DuolingoEntityDescription(
        key="leaderboard_data",
        name="Leaderboard Tier",
        state="tier_name",
        attrs=lambda x: {"Tier": x.get("tier"), "Tier name": x.get("tier_name"), "Streak in tier": x.get("streak_in_tier")},
        icon="mdi:diamond-stone",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DuolingoEntityDescription(
        key="friends_data",
        name="Friends",
        state=lambda x: len(x.get("following")),
        attrs=lambda x: {str(i + 1): f for i, f in enumerate(x.get("following"))},
        icon="mdi:bulletin-board",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DuolingoEntityDescription(
        key="user_data",
        name="Streak",
        state="streak",
        attrs=lambda x: {**x.get("current_streak"), "daily_goal": x.get("daily_goal"), "length": x.get("streak"), "extended_today": x.get("streak_extended_today"), "xp_goal": x.get("xp_goal") if x.get("xp_goal") > 0 else None},
        icon=("mdi:fire", "mdi:fire-off"),
        icon_switch="streak_extended_today",
        entity_category=EntityCategory.DIAGNOSTIC,
        unit="day",
    ),
    DuolingoEntityDescription(
        key="user_data",
        name="Longest Streak",
        state=lambda x: x.get("longest_streak").get("length"),
        attrs=lambda x: x.get("longest_streak"),
        icon="mdi:fire-off",
        entity_category=EntityCategory.DIAGNOSTIC,
        unit="day",
    ),
    DuolingoEntityDescription(
        key="user_data",
        name="Previous Streak",
        state=lambda x: x.get("previous_streak", {}).get("length") if x.get("previous_streak", {}).get("length", -1) > -1 else None,
        attrs=lambda x: x.get("previous_streak") if x.get("previous_streak", {}).get("length", -1) > -1 else {},
        icon="mdi:fire-off",
        entity_category=EntityCategory.DIAGNOSTIC,
        unit="day",
    ),
    DuolingoEntityDescription(
        key="user_data",
        name="Today XP",
        state="xp",
        attrs="xp_week",
        icon=("mdi:fire-off", "mdi:fire"),
        icon_switch=lambda x: x.get("xp") >= x.get("xp_goal"),
        entity_category=EntityCategory.DIAGNOSTIC,
        unit="XP",
    ),
    DuolingoEntityDescription(
        key="quest_data",
        name="Friend Quest",
        state=lambda x: x.get("friends", {}).get("friend", {}).get("display_name") if x.get("friends", {}).get("friend", {}).get("display_name") != "?" else None,
        attrs=lambda x: process_friend_quest(x),
        icon="mdi:account-child",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DuolingoEntityDescription(
        key="quest_data",
        name="Monthly Challenge",
        state=lambda x: x.get("monthly", {}).get("progress") if x.get("monthly", {}).get("progress") > 0 else None,
        attrs=lambda x: x.get("monthly") if x.get("monthly", {}).get("progress") > 0 else {},
        icon="mdi:calendar-multiselect-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    lambda userCoordinator: generate_languages(userCoordinator),
    lambda userCoordinator: generate_friend_streaks(userCoordinator),
]

def process_friend_quest(x):
    q = x.get("friends", {})
    if q.get("friend", {}).get("display_name") == "?":
        return {}
    return {
        "progress": q.get("progress"),
        "increments": q.get("increments"),
        "xp": q.get("xp"),
        "friend_user_id": q.get("friend", {}).get("user_id"),
        "friend_display_name": q.get("friend", {}).get("display_name"),
        "friend_avatar": q.get("friend", {}).get("avatar"),
        "friend_increments": q.get("friend", {}).get("increments"),
        "friend_xp": q.get("friend", {}).get("xp"),
    }

def generate_languages(userCoordinator) -> list[DuolingoEntityDescription]:
    generated = []
    for course in userCoordinator.get("user_data", {}).get("courses", []):
        id = course.get("id")
        if id is None:
            continue
        generated.append(
            DuolingoEntityDescription(
                key="user_data",
                name=f'Language {course.get("name")} ({course.get("from")})',
                state=lambda x, id=id: get_by_item(x.get("courses", []), "id", id, {}).get("xp"),
                attrs=lambda x, id=id: get_by_item(x.get("courses", []), "id", id, {}),
                icon="mdi:flag",
                unit="XP",
                entity_category=EntityCategory.DIAGNOSTIC
            )
        )
    return generated

def generate_friend_streaks(userCoordinator) -> list[DuolingoEntityDescription]:
    generated = []
    for friend_streak in userCoordinator.get("friend_streaks_data", {}).get("confirmed", []):
        id = friend_streak.get("id")
        if id is None:
            continue
        generated.append(
            DuolingoEntityDescription(
                key="friend_streaks_data",
                name=f'Friend Streak {friend_streak.get("friend", {}).get("name", "?")}',
                state=lambda x, id=id: get_by_item(x.get("confirmed", []), "id", id, {}).get("length") if get_by_item(x.get("confirmed", []), "id", id, {}).get("length", -1) > 0 else None,
                attrs=lambda x, id=id: get_by_item(x.get("confirmed", []), "id", id, {}),
                icon=("mdi:fire", "mdi:fire-off"),
                icon_switch=lambda x, id=id: get_by_item(x.get("confirmed", []), "id", id, {}).get("extended", False),
                entity_category=EntityCategory.DIAGNOSTIC,
                unit="day"
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
                userCoordinator = coordinator.data[username] if coordinator.data.get(username) else {}
                for generatedSensor in sensor(userCoordinator):
                    sensor_per_username.append(DuolingoSensor(coordinator, jwt, username, generatedSensor))
            else:
                sensor_per_username.append(DuolingoSensor(coordinator, jwt, username, sensor))
    sensor_per_username.append(DuolingoLeaderboardSensor(
        coordinator,
        jwt,
        usernames,
        DuolingoEntityDescription(
                key="user_data",
                name="Today",
                state=lambda x: x.get("xp") if x.get("xp", -1) > 0 else 0,
                icon="mdi:sort-descending",
                entity_category=EntityCategory.DIAGNOSTIC,
                unit="place",
            )
        ))
    sensor_per_username.append(DuolingoLeaderboardSensor(
        coordinator,
        jwt,
        usernames,
        DuolingoEntityDescription(
                key="user_data",
                name="Week",
                state=lambda x: x.get("week_xp") if x.get("week_xp", -1) > 0 else 0,
                icon="mdi:sort-descending",
                entity_category=EntityCategory.DIAGNOSTIC,
                unit="place",
            )
        ))
    async_add_entities(
        sensor_per_username
    )

