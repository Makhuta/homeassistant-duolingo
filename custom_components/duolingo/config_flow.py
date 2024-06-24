from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigEntry
from homeassistant.core import callback
from homeassistant.const import (
    CONF_USERNAME,
    )
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    ConstantSelector,
    ConstantSelectorConfig
)
from .const import (
    DOMAIN,
    CONF_USERNAME_LABEL,
    CONF_JWT
)
from .helpers import setup_client
from .duolingo_api import (
    FailedToLogin
)
from .options_flow import DuolingoOptionFlow

DUOLINGO_SCHEMA = vol.Schema({
    vol.Optional(CONF_USERNAME + "_label"): ConstantSelector(ConstantSelectorConfig(value=CONF_USERNAME_LABEL)),
    vol.Required(CONF_USERNAME): TextSelector(TextSelectorConfig(multiple=True, multiline=False)),
    vol.Required(CONF_JWT): vol.All(str),
})


class DuolingoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for the Duolingo integration."""
    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> DuolingoOptionFlow:
        return DuolingoOptionFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ):
        errors = {}

        if user_input is not None:
            self._async_abort_entries_match({CONF_JWT: user_input[CONF_JWT]})
            try:
                await self.hass.async_add_executor_job(
                    setup_client,
                    user_input[CONF_USERNAME],
                    user_input[CONF_JWT],
                )
            except FailedToLogin as err:
                errors = {'base': 'failed_to_login'}
            else:
                return self.async_create_entry(title="Duolingo", data=user_input)

        schema = self.add_suggested_values_to_schema(DUOLINGO_SCHEMA, user_input)
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)