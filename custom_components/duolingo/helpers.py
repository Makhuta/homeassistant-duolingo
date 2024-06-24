from homeassistant.core import HomeAssistant
from .duolingo_api import DuolingoAPI
from typing import Any, Dict

def setup_client(
    usernames: list,
    jwt: str
) -> DuolingoAPI:
    clients = []
    for username in usernames:
        try:
            client = DuolingoAPI(username, jwt)
            clients.append(client)
        except:
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