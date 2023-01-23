import logging

import aiohttp
import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, BASE_URL

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
                login_client = LoginClient(user_input)
                await login_client.client()
                valid = True
            except aiohttp.ClientResponseError as exception:
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

    def _configuration_menu(self, step_id: str):
        return self.async_show_menu(
            step_id=step_id,
            menu_options=[
                "finish_configuration",
            ],
        )

    async def async_step_finish_configuration(self, user_input=None):
        _LOGGER.info(f"Configuration from user is finished, input is {self.user_input}")
        # await self.async_set_unique_id(self.user_input[CONF_CLIENT_ID])
        # self._abort_if_unique_id_configured()
        # # will call async_setup_entry defined in __init__.py file
        # return self.async_create_entry(title="ecowatt by RTE", data=self.user_input)


class LoginClient:
    def __init__(self, config):
        self.config = config
        self.token = ""

    async def client(self):
        headers = {"x-application", "CLIENT_PORTAL",
                   "x-provider", "RENAULT"}
        basicAuthorization = aiohttp.helpers.BasicAuth(
            self.config[CONF_USERNAME], self.config[CONF_PASSWORD]
        )

        async with aiohttp.ClientSession() as session:
            async with session.post(BASE_URL, auth=basicAuthorization, headers=headers) as response:
                _LOGGER.debug("Status:", response.status)
                _LOGGER.debug("x-auth-token:", response.headers['x-auth-token'])
        await response.text()
        self.token = response.headers['x-auth-token']
        _LOGGER.debug("Fetched a token from OBS auth")
        return session
