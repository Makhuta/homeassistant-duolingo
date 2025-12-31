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
        return self.lingo.update()

class FailedToLogin(Exception):
    "Raised when the Duolingo user fail to Log-in"
    pass