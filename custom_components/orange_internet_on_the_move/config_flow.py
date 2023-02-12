import logging

import voluptuous as vol
from homeassistant import config_entries

from .OBSHttpClient import ObsHttpClient, ApiAuthError
from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)
DATA_SCHEMA = {
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
}


class SetupConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Called once with None as user_input, then a second time with user provided input"""
        errors = {}
        valid = False

        if user_input is not None:
            _LOGGER.debug(f"User input is {user_input}")
            _LOGGER.info("Testing connectivity to OBS api")
            try:
                obs_http_client = ObsHttpClient(config=user_input, hass=self.hass)
                await obs_http_client.authenticate_and_store_token()
                valid = True
            except ApiAuthError as exception:
                _LOGGER.error(f"Error while login to Orange API. Credentials are likely incorrect : {exception}")
                errors["base"] = "auth_error"
            except Exception as e:
                _LOGGER.error(f"Error while login to Orange API, unknown error: {e}")
                errors["base"] = "generic_error"
            if valid:
                _LOGGER.debug("Connectivity to Orange API validated")
                return self.async_create_entry(title="Orange Internet on the move Data", data=user_input)
        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(step_id="user", data_schema=vol.Schema(DATA_SCHEMA), errors=errors)
