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
    TIER_LIST,
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
            {"key": "avatar", "name": "avatar", "value": lambda x: "https:" + str(x) + "/large"},
            ],
        icon="mdi:account",
        entity_category=EntityCategory.DIAGNOSTIC,
        unit="XP"
    ),
    DuolingoEntityDescription(
        key="user_info",
        name="Gems",
        state="gems",
        icon="mdi:diamond",
        entity_category=EntityCategory.DIAGNOSTIC,
        unit="Gems"
    ),
    DuolingoEntityDescription(
        key="leaderboard",
        name="Leaderboard",
        state="position",
        attrs=lambda x: {(id + 1): {camel_to_snake(key): value for key, value in x.get("board")[id].items() if key in ["display_name", "has_plus", "has_recent_activity_15", "score", "streak_extended_today", "user_id", "avatar_url"]} for id in range(len(x.get("board")))},
        icon="mdi:bulletin-board",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DuolingoEntityDescription(
        key="leaderboard",
        name="Leaderboard Tier",
        state=lambda x: TIER_LIST.get(str(x.get("tier.tier")), x.get("tier.tier")),
        attrs=lambda x: {"Tier": x.get("tier.tier"), "Tier name": TIER_LIST.get(str(x.get("tier.tier")), "Unknown"), "Streak in tier": x.get("tier.streak_in_tier")},
        icon="mdi:diamond-stone",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DuolingoEntityDescription(
        key="friends",
        name="Friends",
        state=lambda x: len(x),
        attrs=lambda x: {friend.get("displayName", friend.get("username")): {camel_to_snake(key): value if key != "picture" else (value + "/large") for key, value in friend.items() if key in ["displayName", "hasSubscription", "isCurrentlyActive", "totalXp", "userId", "username", "picture"]} for friend in x},
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
    DuolingoEntityDescription(
        key="daily_xp",
        name="Today XP",
        state=lambda x: x.get("last", 0),
        attrs=lambda x: {item: x[item] for item in x if item != "last"},
        icon=("mdi:fire-off", "mdi:fire"),
        icon_switch=lambda x: x.get("last", 0) == 0,
        entity_category=EntityCategory.DIAGNOSTIC,
        unit="XP",
    ),
    DuolingoEntityDescription(
        key="quests",
        name="Friend Quest",
        state=lambda x: get_prefix(x, "friend_quest").get("user.name", "unknown"),
        attrs=lambda x: {key.replace(".", "_"): get_prefix(x, "friend_quest").get(key) for key in get_prefix(x, "friend_quest").keys()},
        icon="mdi:account-child",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DuolingoEntityDescription(
        key="quests",
        name="Monthly Challenge",
        state=lambda x: get_prefix(x, "monthly_challenge").get("progress"),
        attrs=lambda x: get_prefix(x, "monthly_challenge"),
        icon="mdi:calendar-multiselect-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    lambda userCoordinator: generate_languages(userCoordinator),
    lambda userCoordinator: generate_friend_streaks(userCoordinator),
]

def generate_languages(userCoordinator) -> list[DuolingoEntityDescription]:
    languages_details = userCoordinator.get("languages_details", {})
    generated = []
    for key, value in languages_details.items():
        if key.endswith("id"):
            langKey = value
            langString = languages_details.get(f'{langKey}.language_string', langKey)
            langFrom = languages_details.get(f'{langKey}.from', "??")

            generated.append(
                DuolingoEntityDescription(
                    key="languages_details",
                    name=f'Language {langString.capitalize()} ({langFrom})',
                    state=f'{langKey}.points',
                    attrs=(lambda lang: (lambda x: {k: x.get(f'{lang}.{k}') for k in ["language_string", "points", "language", "from", "current_learning", "id"] if x.get(f'{lang}.{k}')}))(langKey),
                    icon="mdi:flag",
                    unit="XP",
                    entity_category=EntityCategory.DIAGNOSTIC
                )
            )

    return generated

def get_by_item(l, key, value, default=None):
    for item in l:
        if item[key] == value:
            return item
    return default

def generate_friend_streaks(userCoordinator) -> list[DuolingoEntityDescription]:
    friends_streaks = userCoordinator.get("friends_streaks")

    generated = []
    if friends_streaks is None:
        return generated
    for friend_streak in friends_streaks.get():
        id = friend_streak.get("id")
        if id is None:
            continue
        generated.append(
            DuolingoEntityDescription(
                key="friends_streaks",
                name=f'Friend Streak {friend_streak.get("name", "unknown")}',
                state=lambda x, id=id: get_by_item(x, "id", id, {}).get("length", 0),
                attrs=lambda x, id=id: get_by_item(x, "id", id, {}),
                icon=("mdi:fire", "mdi:fire-off"),
                icon_switch=lambda x, id=id: get_by_item(x, "id", id, {}).get("extended", False),
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
                userCoordinator = {**coordinator.data[username]} if coordinator.data.get(username) else {}
                for generatedSensor in sensor(userCoordinator):
                    sensor_per_username.append(DuolingoSensor(coordinator, jwt, username, generatedSensor))
            else:
                sensor_per_username.append(DuolingoSensor(coordinator, jwt, username, sensor))

    sensor_per_username.append(DuolingoLeaderboardSensor(
        coordinator,
        jwt,
        usernames,
        DuolingoEntityDescription(
                key="daily_xp",
                name="Today",
                state=lambda x: x.get("last", 0),
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
                key="daily_xp",
                name="Week",
                state=lambda x: sum([x[day] for day in add_weekly_xp(x)]),
                icon="mdi:sort-descending",
                entity_category=EntityCategory.DIAGNOSTIC,
                unit="place",
            )
        ))
    async_add_entities(
        sensor_per_username
    )

