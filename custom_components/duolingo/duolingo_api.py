from .duolingo import Duolingo
from typing import Any, Dict
from collections.abc import Callable
from functools import reduce

class DataObject():
    def __init__(self, dict: Dict[str, Any] = {}):
        self.data = self._convert(dict)

    def _convert(self, object) -> Dict[str, Any]:
        if type(object) == dict:
            obj = {}
            for keyOuter, valueOuter in object.items():
                converted = self._convert(valueOuter)
                if type(converted) == dict:
                    for keyInner, valueInner in converted.items():
                        obj[f'{keyOuter}.{keyInner}'] = valueInner
                else:
                    obj[keyOuter] = converted
            return obj
        return object

    def _exist(self, key) -> bool:
        return key in list(self.data.keys())

    def _remove_prefix(self, value, prefix) -> str:
        if value.startswith(prefix):
            return value[len(prefix):]
        return value

    def get(self, key:str = None, default = None) -> Any:
        if not key:
            return self.data
        if self._exist(key):
            return self.data[key]
        
        output = {}
        for k, value in self.data.items():
            if k.startswith(key):
                output[self._remove_prefix(k, f'{key}.')] = value

        return output if len(list(output.keys())) > 0 else default
    
    def items(self) -> list:
        return self.data.items()

import logging
_LOGGER = logging.getLogger(__name__)

class DuolingoAPI():
    def __init__(self, username=None, jwt=None, internal=30):
        self.username = username
        self.interval = internal
        try:
            self.lingo = Duolingo(username=username, jwt=jwt)
        except:
            raise FailedToLogin

    def get_username(self):
        return self.username

    def get_interval(self):
        return self.interval

    def update(self):
        functions = {
            "user_info": lambda: {**self.lingo.get_user_info(), "languages": [value["language_string"] for key, value in self.lingo.get_languages_details().items() if value.get("language_string")]},
            "quests": self.lingo.get_quests,
            "languages_details": self.lingo.get_languages_details,
            "leaderboard": lambda:{"board": self.lingo.get_leaderboard(), "position": self.lingo.get_leaderboard_position(), "tier": self.lingo.get_leaderboard_tier()},
            "streak_info": self.lingo.get_streak_info,
            "friends": self.lingo.get_friends,
            "friends_streaks": self.lingo.get_friend_streaks,
            "daily_xp": self.lingo.get_daily_xp,
        }

        data = {}

        try:
            self.lingo.update_user_data()
        except Exception as err:
            _LOGGER.err(err)
            pass
        for (key, function) in functions.items():
            try:
                data[key] = DataObject(function())
            except Exception as err:
                _LOGGER.error(f'{key} errored')
                _LOGGER.error(err)
                data[key] = DataObject()

        return data


class FailedToLogin(Exception):
    "Raised when the Duolingo user fail to Log-in"
    pass