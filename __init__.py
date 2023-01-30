"""init integration Orange Internet on the move."""
import logging

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .dto import ConsumptionOfDevice
from .const import (
    DOMAIN, CONF_USERNAME, CONF_PASSWORD, BASE_URL, ENDPOINT_USER, ENDPOINT_HEADER_PROVIDER,
    ENDPOINT_HEADER_APPLICATION, ENDPOINT_LOGIN, ENDPOINT_DEVICES, ENDPOINT_DEVICE_CONSUMPTION,
)

DATA_SCHEMA = {
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_PASSWORD): str,
}

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Called async setup entry from __init__.py")
    _LOGGER.debug(f"Async setup entry with config data {entry.data}")

    hass.data.setdefault(DOMAIN, {})

    # here we store the coordinator for future access
    if entry.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][entry.entry_id] = {}
    hass.data[DOMAIN][entry.entry_id] = ObsHttpClient(dict(entry.data))

    # will make sure async_setup_entry from sensor.py is called
    hass.config_entries.async_setup_platforms(entry, [Platform.SENSOR])

    # subscribe to config updates
    entry.async_on_unload(entry.add_update_listener(update_entry))

    return True


async def update_entry(hass, entry):
    """
    This method is called when options are updated
    We trigger the reloading of entry (that will eventually call async_unload_entry)
    """
    _LOGGER.debug("update_entry method called")
    # will make sure async_setup_entry from sensor.py is called
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """This method is called to clean all sensors before re-adding them"""
    _LOGGER.debug("async_unload_entry method called")
    unload_ok = await hass.config_entries.async_unload_platforms(entry, [Platform.SENSOR])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


# TODO Duplicate from config_flow
class ObsHttpClient:
    def __init__(self, config):
        self.config = config
        self.token = ""
        _LOGGER.debug(f"ObsHttpClient config is {config}")

    async def get_auth_token(self):
        additional_headers = [{"x-application", ENDPOINT_HEADER_APPLICATION},
                              {"x-provider", ENDPOINT_HEADER_PROVIDER}]
        basic_authorization = aiohttp.helpers.BasicAuth(self.config[CONF_USERNAME], self.config[CONF_PASSWORD])

        _LOGGER.debug("get_auth_token")
        async with aiohttp.ClientSession() as session:
            async with session.post(BASE_URL + ENDPOINT_LOGIN,
                                    auth=basic_authorization,
                                    headers=additional_headers) as response:
                _LOGGER.debug("Status:", response.status)
                _LOGGER.debug("x-auth-token:", response.headers['x-auth-token'])
        await response.text()
        self.token = response.headers['x-auth-token']
        _LOGGER.debug("Fetched a token from OBS auth")
        return self.token

    async def get_user_info(self):
        additional_headers = [
            {"x-application", ENDPOINT_HEADER_APPLICATION},
            {"x-provider", ENDPOINT_HEADER_PROVIDER},
            {"x-auth-token", self.token},
        ]
        async with aiohttp.ClientSession() as session:
            async with session.get(BASE_URL + ENDPOINT_USER, headers=additional_headers) as response:
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

    async def get_devices_info(self):
        additional_headers = [
            {"x-application", ENDPOINT_HEADER_APPLICATION},
            {"x-provider", ENDPOINT_HEADER_PROVIDER},
            {"x-auth-token", self.token},
        ]
        async with aiohttp.ClientSession() as session:
            async with session.get(BASE_URL + ENDPOINT_DEVICES, headers=additional_headers) as response:
                _LOGGER.debug("Status:", response.status)
        device_info_response = await response.json()
        _LOGGER.debug(f"Fetched user info {device_info_response}")
        _LOGGER.debug(f"Select first object device {device_info_response[0]}")
        return device_info_response[0]

    # id
    # country
    # status
    # tag
    # user: object
    # notification: object
    # puk
    # serial_number
    # creation_date

    async def get_device_id(self, device_info_response):
        return device_info_response[0].id

    async def get_consumption_of_device(self, device) -> ConsumptionOfDevice:
        additional_headers = [
            {"x-application", ENDPOINT_HEADER_APPLICATION},
            {"x-provider", ENDPOINT_HEADER_PROVIDER},
            {"x-auth-token", self.token},
        ]
        device_id = await self.get_device_id(device)
        async with aiohttp.ClientSession() as session:
            async with session.get(BASE_URL + ENDPOINT_DEVICES + "/" + device_id + ENDPOINT_DEVICE_CONSUMPTION,
                                   headers=additional_headers) as response:
                _LOGGER.debug("Status:", response.status)
        device_consumption_response = await response.json()
        _LOGGER.debug(f"Fetched user info {device_consumption_response}")
        first_device = device_consumption_response[0]
        _LOGGER.debug(f"Select first object device consumption {first_device}")
        return ConsumptionOfDevice(first_device.type,
                                   first_device.initial_data,
                                   first_device.left_data,
                                   first_device.expiry_date,
                                   first_device.start_date,
                                   )

        # type
        # initial_data
        # left_data
        # expiry_date
        # start_date
