import voluptuous as vol
import logging

from typing import Any
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from .const import(
    DOMAIN,
    CONF_CUSTOM_INJ_TARIFF,
    CONF_CUSTOM_PRICE,
    CONF_FIXED_INJ_PRICE,
    CONF_FIXED_PRICE,
    CONF_INJ_TARIFF_FACTOR,
    CONF_PRICE_FACTOR,
    CONF_USER_STEP,
)

_LOGGER = logging.getLogger(__name__)

PRICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PRICE_FACTOR): vol.Coerce(float),
        vol.Required(CONF_FIXED_PRICE): vol.Coerce(float),
    }
)

INJ_TARIFF_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_INJ_TARIFF_FACTOR): vol.Coerce(float),
        vol.Required(CONF_FIXED_INJ_PRICE): vol.Coerce(float),
    }
)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CUSTOM_PRICE): cv.boolean,
        vol.Required(CONF_CUSTOM_INJ_TARIFF): cv.boolean,
    }
)

class SdacEliaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Example config flow."""
    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    
    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
        """Invoked when a user initiates a flow via the user interface."""
        errors = {}
        self.data = {}
        if user_input is not None:
            try:
                validated_schema = USER_SCHEMA(user_input)
                
            except Exception as e:
                _LOGGER.error(e)
                errors["base"] = "invalid_input"
            
            if not errors:
                self.data[CONF_USER_STEP] = user_input
                if self.data[CONF_USER_STEP][CONF_CUSTOM_PRICE]:
                    return await self.async_step_custom_price()
                elif self.data[CONF_USER_STEP][CONF_CUSTOM_INJ_TARIFF]:
                    return await self.async_step_custom_inj_tariff()
                else:
                    return self.async_create_entry(title=DOMAIN, data=self.data)

        return self.async_show_form(step_id="user", data_schema=USER_SCHEMA, errors=errors)
    
    async def async_step_custom_price(self, user_input: dict[str, Any] | None = None):
        errors = {}
        if user_input is not None:
            try:
                validated_schema = PRICE_SCHEMA(user_input)
            
            except Exception as e:
                _LOGGER.error(e)
                errors["base"] = "invalid_input"

            if not errors:
                self.data[CONF_CUSTOM_PRICE] = user_input
                if self.data[CONF_USER_STEP][CONF_CUSTOM_INJ_TARIFF]:
                    return await self.async_step_custom_inj_tariff()
                else:
                    return self.async_create_entry(title=DOMAIN, data=self.data)
        
        return self.async_show_form(step_id="custom_price", data_schema=PRICE_SCHEMA, errors=errors)
    
    async def async_step_custom_inj_tariff(self, user_input: dict[str, Any] | None = None):
        errors = {}
        if user_input is not None:
            try:
                validated_schema = INJ_TARIFF_SCHEMA(user_input)

            except vol.Invalid as e:
                errors["base"] = "invalid_input"
                _LOGGER.error(e)
            
            if not errors:
                self.data[CONF_CUSTOM_INJ_TARIFF] = user_input
                return self.async_create_entry(title=DOMAIN, data=self.data)
        
        return self.async_show_form(step_id="custom_inj_tariff", data_schema=INJ_TARIFF_SCHEMA, errors=errors)