import logging

import aiohttp
import voluptuous as vol
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_USERNAME, CONF_PASSWORD, BASE_URL, ENDPOINT_USER, ENDPOINT_HEADER_PROVIDER,
    ENDPOINT_HEADER_APPLICATION, ENDPOINT_LOGIN, ENDPOINT_DEVICES, ENDPOINT_DEVICE_CONSUMPTION,
)
from .dto import ConsumptionOfDevice, Device

DATA_SCHEMA = {
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
}

_LOGGER = logging.getLogger(__name__)


class ApiAuthError(BaseException):
    pass


class ObsHttpClient:
    def __init__(self, hass, config):
        self.hass = hass
        self.config = config
        self.auth_token = None
        _LOGGER.debug(f"ObsHttpClient config is {config}")

    async def authenticate_and_store_token(self) -> None:
        basic_authorization = aiohttp.helpers.BasicAuth(self.config[CONF_USERNAME], self.config[CONF_PASSWORD])
        authorization_encoded = basic_authorization.encode()
        additional_headers = {
            "x-application": ENDPOINT_HEADER_APPLICATION,
            "x-provider": ENDPOINT_HEADER_PROVIDER,
            "Authorization": authorization_encoded
        }

        _LOGGER.debug(f"authenticate_and_store_token with {additional_headers} and {basic_authorization}")
        endpoint_login = BASE_URL + ENDPOINT_LOGIN
        _LOGGER.debug(f"authenticate_and_store_token on {endpoint_login}")

        session = async_get_clientsession(self.hass)
        response = await session.post(endpoint_login, headers=additional_headers)
        _LOGGER.debug(f"Status: {response.status}")
        if response.status != 200:
            raise ApiAuthError
        _LOGGER.debug("x-auth-token:", response.headers['x-auth-token'])

        self.auth_token = response.headers['x-auth-token']
        _LOGGER.debug(f"Fetched a token from OBS auth : {self.auth_token}")

    # not used
    async def get_user_info(self):
        _LOGGER.debug(f"get_user_info called")
        session = async_get_clientsession(self.hass)
        response = await session.get(BASE_URL + ENDPOINT_USER, headers=self.get_additional_header())
        _LOGGER.debug("Status:", response.status)
        user_info_response = await response.json()
        _LOGGER.debug(f"Fetched user info {user_info_response}")

        return user_info_response

    #     id: str
    #     email: str
    #     role: str
    #     firstname: str
    #     lastname: str
    #     type: str
    #     enabled: str
    #     creation_date: str

    def get_additional_header(self):
        return {
            "x-application": ENDPOINT_HEADER_APPLICATION,
            "x-provider": ENDPOINT_HEADER_PROVIDER,
            "x-auth-token": self.auth_token,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Host": "internetonthemove.orange-business.com",
        }

    async def get_first_device_info(self) -> Device:
        _LOGGER.debug(f"get_devices_info called with auth token {self.auth_token}")

        endpoint_devices = BASE_URL + ENDPOINT_DEVICES
        _LOGGER.debug(f"calling endpoint {endpoint_devices}")
        session = async_get_clientsession(self.hass)
        response = await session.get(endpoint_devices, headers=self.get_additional_header())
        _LOGGER.debug("Status:", response.status)
        device_info_response = await response.json()
        _LOGGER.debug(f"Fetched user info {device_info_response}")
        first_device_response = device_info_response[0]
        _LOGGER.debug(f"Select first object device {first_device_response}")
        return Device(first_device_response["id"],
                      first_device_response["country"],
                      first_device_response["status"],
                      first_device_response["tag"],
                      first_device_response["user"]["id"],
                      first_device_response["user"]["name"],
                      first_device_response["creation_date"],
                      first_device_response["serial_number"]
                      )

    # id
    # country
    # status
    # tag
    # user: object
    # notification: object
    # puk
    # serial_number
    # creation_date

    async def get_consumption_of_device(self, device: Device) -> ConsumptionOfDevice:
        _LOGGER.debug(f"get_consumption_of_device called")
        consumption_endpoint = BASE_URL + ENDPOINT_DEVICES + "/" + device.device_id + ENDPOINT_DEVICE_CONSUMPTION
        _LOGGER.debug(f"Calling endpoint {consumption_endpoint}")
        session = async_get_clientsession(self.hass)
        response = await session.get(consumption_endpoint, headers=self.get_additional_header())
        _LOGGER.debug("Status:", response.status)
        device_consumption_response = await response.json()
        _LOGGER.debug(f"Fetched consumption {device_consumption_response}")
        first_device = device_consumption_response[0]
        _LOGGER.debug(f"Select first object device consumption {first_device}")
        return ConsumptionOfDevice(first_device["type"],
                                   first_device["initial_data"],
                                   first_device["left_data"],
                                   first_device["expiry_date"],
                                   first_device["start_date"],
                                   )

        # type
        # initial_data
        # left_data
        # expiry_date
        # start_date
