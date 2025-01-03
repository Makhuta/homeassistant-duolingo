from typing import Any
from homeassistant.config_entries import OptionsFlow, ConfigEntry, ConfigFlowResult
import voluptuous as vol

from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    ConstantSelector,
    ConstantSelectorConfig,
)
from homeassistant.const import (
    CONF_USERNAME,
    )
from .const import (
    DOMAIN, 
    CONF_USERNAME_LABEL,
    CONF_INTERVAL,
    )


class DuolingoOptionFlow(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry


    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors = {}

        coordinator = self.hass.data[DOMAIN][self._config_entry.entry_id]

        if user_input is not None:
            # Validate and process user input here
            updated_data = {
                **self._config_entry.data,
                CONF_USERNAME: user_input.get(CONF_USERNAME),
                CONF_INTERVAL: user_input.get(CONF_INTERVAL),
            }
            self.hass.config_entries.async_update_entry(self._config_entry, data=updated_data, minor_version=0, version=1)

            return self.async_create_entry(title="", data=updated_data)

        DUOLINGO_SCHEMA = vol.Schema({
            vol.Optional(CONF_USERNAME + "_label"): ConstantSelector(ConstantSelectorConfig(value=CONF_USERNAME_LABEL)),
            vol.Required(CONF_USERNAME, default=self._config_entry.data.get(CONF_USERNAME, [])): TextSelector(TextSelectorConfig(multiple=True, multiline=False)),
            vol.Required(CONF_INTERVAL, default=self._config_entry.data.get(CONF_INTERVAL, 30)): vol.All(vol.Coerce(int), vol.Range(min=10)),
        })

        # Display a form to gather user input
        return self.async_show_form(step_id="init", data_schema=DUOLINGO_SCHEMA, errors=errors)