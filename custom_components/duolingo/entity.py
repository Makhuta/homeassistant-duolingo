from typing import Any, Dict, Optional
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import EntityCategory

from .const import DOMAIN, functionType
from .coordinator import DuolingoDataCoordinator
from .duolingo_api import DataObject

import logging
_LOGGER = logging.getLogger(__name__)


def sanitize_dict(fields):
    """Ensure all field keys are strings."""
    return {str(k): v for k, v in fields.items()}

class DuolingoEntityDescription():
    def __init__(
        self,
        key: str,
        name: str,
        state: str | Callable | None = None,
        attrs: str | Callable | list | None = None,
        icon: str | tuple | None = None,
        icon_switch: str | None = None,
        unit: str | None = None,
        entity_category: EntityCategory | None = None
    ):
        self.key = key
        self.name = name
        self.attrs = attrs
        self.state = state
        self.icon = icon
        self.icon_switch = icon_switch
        self.unit = unit
        self.entity_category = entity_category

class DuolingoSensor(CoordinatorEntity[DuolingoDataCoordinator], SensorEntity):
    def __init__(self, coordinator: DuolingoDataCoordinator, jwt: str, username: str, description: DuolingoEntityDescription):
        super().__init__(coordinator)
        self._username = username
        self._jwt = jwt
        self._description = description
        self.entity_id = f'sensor.{username}_duolingo_{description.name.lower().replace(" ", "_")}'
        self._attr_entity_category = description.entity_category
        self._state = None
        self._attrs = {}

    def _get_user_data(self) -> DataObject:
        return self.coordinator.data.get(self._username)
        return DataObject({**self.coordinator.data[self._username]}) if self.coordinator.data.get(self._username) else DataObject()

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f'{self._username} {self._description.name}'

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f'{self._jwt}_Duolingo_{self._username}_{self._description.name}'

    @property
    def icon(self):
        if type(self._description.icon) == tuple:
            if len(self._description.icon) > 1 and self._description.icon_switch:
                user_data = self._get_user_data()
                if user_data:
                    sensor_category = user_data.get(self._description.key)
                    if sensor_category:
                        if type(self._description.icon_switch) == str:
                            return self._description.icon[0 if sensor_category.get(self._description.icon_switch) else 1]
                        if type(self._description.icon_switch) == functionType:
                            return self._description.icon[0 if self._description.icon_switch(sensor_category) else 1]

            return None
        
        return self._description.icon

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._description.unit

    @property
    def device_info(self) -> Dict[str, Any]:
        return {
            "name": self._username,
            "manufacturer": "Duolingo",
            "model": "Scrapper",
            "identifiers": {(DOMAIN, f'{self._jwt}_Duolingo_{self._username}')},
            "configuration_url": self._attrs.get("entity_picture"),
        }

    def update_state(self):
        try:
            user_data = self._get_user_data()
            if user_data:
                sensor_category = user_data.get(self._description.key)
                if sensor_category:
                    if type(self._description.state) == str:
                        self._state = sensor_category.get(self._description.state)
                    if type(self._description.state) == functionType:
                        self._state = self._description.state(sensor_category)
        except Exception as e:
            _LOGGER.error(e)

    @property
    def state(self) -> Optional[str]:
        """Return the value of the sensor."""
        self.update_state()
        return self._state

    def update_attributes(self):
        try:
            user_data = self._get_user_data()
            if user_data:
                attrs = self._description.attrs
                sensor_category = user_data.get(self._description.key)
                if sensor_category:
                    if type(attrs) == str:
                        self._attrs = sensor_category.get(attrs)
                    if type(attrs) == list:
                        output = {}
                        for attr in attrs:
                            data = sensor_category.get(attr.get("key"))
                            if data:
                                if not attr.get("name"):
                                    continue
                                if "value" in list(attr.keys()):
                                    if attr.get('name') == 'avatar':
                                        # Set the entity_picture attribute for use with entity badge and similar Lovelace cards
                                        # FIXME: Should this completely replace the avatar as an if/else statement?
                                        #        Would need to co-ordinate such a change with https://github.com/Makhuta/lovelace-duolingo-card
                                        output['entity_picture'] = attr.get('value')(data)
                                    output[attr.get("name")] = attr.get("value")(data)
                                else:
                                    output[attr.get("name")] = data
                        self._attrs = output
                    if type(attrs) == functionType:
                        self._attrs = attrs(sensor_category)
        except Exception as e:
            _LOGGER.error(e)

    @property
    def extra_state_attributes(self) -> Dict[str, Any] | None:
        self.update_attributes()
        return sanitize_dict(self._attrs)




class DuolingoLeaderboardSensor(CoordinatorEntity[DuolingoDataCoordinator], SensorEntity):
    def __init__(self, coordinator: DuolingoDataCoordinator, jwt: str, usernames: list, description: DuolingoEntityDescription):
        super().__init__(coordinator)
        self._usernames = usernames
        self._jwt = jwt
        self._description = description
        self.entity_id = f'sensor.leaderboard_duolingo_{description.name.lower().replace(" ", "_")}'
        self._attr_entity_category = description.entity_category
        self._state = None
        self._attrs = {}
        self._data = []

    def _get_users_data(self) -> list:
        return [{"data": self.coordinator.data.get(username), "username": username} for username in self._usernames]
        return [DataObject({**self.coordinator.data[username], "username": username}) if self.coordinator.data.get(username) else DataObject() for username in self._usernames]

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f'Leaderboard {self._description.name}'

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f'{self._jwt}_Duolingo_Leaderboard_{self._description.name}'

    @property
    def icon(self):
        return self._description.icon

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._description.unit

    @property
    def device_info(self) -> Dict[str, Any]:
        return {
            "name": "Leaderboard",
            "manufacturer": "Duolingo",
            "model": "Scrapper",
            "identifiers": {(DOMAIN, f'{self._jwt}_Duolingo_Leaderboard')},
        }

    def update(self):
        try:
            users_data = self._get_users_data()
            out_datas = []
            for user_data in users_data:
                category = user_data.get("data", {}).get(self._description.key)
                username = user_data.get("data", {}).get("username")
                if category is None:
                    continue
                avatar = category.get("avatar")
                fullname = category.get("fullname") if user_data.get("data", {}).get("user_info") != "?" else None
                leaderboard = user_data.get("data", {}).get("leaderboard_data")
                is_main = leaderboard is not None and leaderboard.get("position") is not None and leaderboard.get("position") > 0
                state = {}
                if type(self._description.state) == str:
                    state = { "username": username, "fullname": fullname, "xp": category.get(self._description.state), "avatar": avatar, "is_main": is_main}
                if type(self._description.state) == functionType:
                    state = { "username": username, "fullname": fullname, "xp": self._description.state(category), "avatar": avatar, "is_main": is_main}
                        
                out_datas.append(state)

            attrs = {}
            for id, out_data in enumerate(sorted(out_datas, key=lambda x: (-x["xp"], x["username"])), start=1):
                if out_data["is_main"]:
                    self._state = id
                attrs[f'{id}'] = {key: out_data[key] for key in out_data if key in ["xp", "username", "avatar", "fullname"]}

            self._attrs = attrs
        except Exception as e:
            _LOGGER.error(e)

    @property
    def state(self) -> Optional[str]:
        """Return the value of the sensor."""
        self.update()
        return self._state

    @property
    def extra_state_attributes(self) -> Dict[str, Any] | None:
        self.update()
        return sanitize_dict(self._attrs)