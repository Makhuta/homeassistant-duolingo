from homeassistant.core import HomeAssistant
from .duolingo_api import DuolingoAPI
from typing import Any, Dict
import re

import logging
_LOGGER = logging.getLogger(__name__)

def setup_client(
    usernames: list,
    jwt: str,
    interval: int = 30
) -> DuolingoAPI:
    clients = []
    for username in usernames:
        try:
            client = DuolingoAPI(username, jwt, interval)
            clients.append(client)
        except:
            _LOGGER.warn(f'There was error during initializing {username} user.')
            pass
    return clients


def convert_objects(data) -> Dict[str, Any]:
    if type(data) == dict:
        obj = {}
        for (keyOuter, valueOuter) in data.items():
            converted = convert_objects(valueOuter)
            if type(converted) == dict:
                for (keyInner, valueInner) in converted.items():
                    obj[f'{keyOuter}_{keyInner}'] = valueInner
            else:
                obj[keyOuter] = converted
        return obj
        
    return data

def camel_to_snake(name: str) -> str:
    s1 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
    return s1.lower()