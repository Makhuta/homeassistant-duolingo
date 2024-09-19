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

    def _get_user_data(self) -> DataObject:
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
                            return self._description.icon[0 if self._description.icon_switch(sensor_category.get()) else 1]

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
        }

    @property
    def state(self) -> Optional[str]:
        """Return the value of the sensor."""
        try:
            user_data = self._get_user_data()
            if user_data:
                sensor_category = user_data.get(self._description.key)
                if sensor_category:
                    if type(self._description.state) == str:
                        return sensor_category.get(self._description.state)
                    if type(self._description.state) == functionType:
                        return self._description.state(sensor_category.get())
        except Exception as e:
            _LOGGER.err(e)
            return None
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        try:
            user_data = self._get_user_data()
            if user_data:
                attrs = self._description.attrs
                sensor_category = user_data.get(self._description.key)
                if sensor_category:
                    if type(attrs) == str:
                        return sensor_category.get(attrs)
                    if type(attrs) == list:
                        output = {}
                        for attr in attrs:
                            data = sensor_category.get(attr.get("key"))
                            if data:
                                if not attr.get("name"):
                                    continue
                                if "value" in list(attr.keys()):
                                    output[attr.get("name")] = attr.get("value")(data)
                                else:
                                    output[attr.get("name")] = data
                        return output
                    if type(attrs) == functionType:
                        return attrs(sensor_category.get())
        except Exception as e:
            _LOGGER.err(e)
            return {}
        return {}