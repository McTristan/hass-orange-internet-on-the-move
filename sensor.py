"""Platform for sensor integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfInformation
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from .dto import ConsumptionOfDevice
from .const import (
    DOMAIN, )

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback
) -> None:
    _LOGGER.info("Called async setup entry")
    """Set up the sensor platform."""

    # assuming API object stored here by __init__.py
    obs_api = hass.data[DOMAIN][entry.entry_id]
    obs_coordinator: OBSCoordinator = OBSCoordinator(hass, obs_api)

    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    #
    # If you do not want to retry setup on failure, use
    # coordinator.async_refresh() instead
    #
    _LOGGER.info("Calling async_config_entry_first_refresh")
    await obs_coordinator.async_config_entry_first_refresh()

    _LOGGER.info(f"async_add_entities with {obs_coordinator.data}")
    new_devices = [DataSensorEntity(obs_coordinator, obs_coordinator.data),
                   DataConsumedSensorEntity(obs_coordinator, obs_coordinator.data)]
    _LOGGER.info(f"async_add_entities new_devices={new_devices}")
    if new_devices:
        async_add_entities(new_devices)
    _LOGGER.info("async_add_entities done")


"""
class DataSensor(SensorEntity):

    def __init__(self, obs_coordinator: OBSAPICoordinator, hass: HomeAssistant):
        self._attr_name = "Data contract"
        self._attr_native_unit_of_measurement = UnitOfInformation.KILOBYTES
        self._attr_device_class = SensorDeviceClass.DATA_SIZE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self.coordinator = obs_coordinator
        super().__init__(hass=hass)

    @property
    def unique_id(self) -> str:
        return f"orange-internet-on-the-move-subscription"

    def update(self) -> None:
        self.coordinator.
        self._attr_native_value = 1048576


        SensorEntityDescription(
            key="data_limit",
            name="Data limit",
            native_unit_of_measurement=UnitOfInformation.KILOBITS,
            device_class=SensorDeviceClass.DATA_SIZE,
            icon="mdi:download",
        ),
        SensorEntityDescription(
            key="data_remaining",
            name="Data remaining",
            native_unit_of_measurement=UnitOfInformation.KILOBITS,
            device_class=SensorDeviceClass.DATA_SIZE,
            icon="mdi:download",
        )
"""


class DataConsumedSensorEntity(CoordinatorEntity, SensorEntity):
    """An entity using CoordinatorEntity.

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """

    def __init__(self, coordinator, data_plan: ConsumptionOfDevice):
        _LOGGER.info(f"Creating DataSensorEntity with {data_plan}")
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=data_plan)
        self._attr_name = "Data consummed"
        self._attr_native_unit_of_measurement = UnitOfInformation.KILOBYTES
        self._attr_device_class = SensorDeviceClass.DATA_SIZE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_value = data_plan.left_data

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        new_state_value = self.coordinator.data[self._attr_native_value]["state"]
        _LOGGER.info(f"_handle_coordinator_update previous : {self._attr_native_value} new {new_state_value}")
        self._attr_native_value = new_state_value
        self.async_write_ha_state()


class DataSensorEntity(CoordinatorEntity, SensorEntity):
    """An entity using CoordinatorEntity.

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """

    def __init__(self, coordinator, data_plan: ConsumptionOfDevice):
        _LOGGER.info(f"Creating DataSensorEntity with {data_plan}")
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=data_plan)
        self._attr_name = "Data Plan"
        self._attr_native_unit_of_measurement = UnitOfInformation.KILOBYTES
        self._attr_device_class = SensorDeviceClass.DATA_SIZE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_value = data_plan.initial_data

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        new_state_value = self.coordinator.data[self._attr_native_value]["state"]
        _LOGGER.info(f"_handle_coordinator_update previous : {self._attr_native_value} new {new_state_value}")
        self._attr_native_value = new_state_value
        self.async_write_ha_state()


class OBSCoordinator(DataUpdateCoordinator[ConsumptionOfDevice]):
    """A coordinator to fetch data from the api only once"""

    def __init__(self, hass, obs_api_client):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Orange Internet on the move sensor",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=60),
        )
        self.obs_api_client = obs_api_client

    async def _async_update_data(self):
        _LOGGER.debug("Starting collecting data")
        _LOGGER.debug("Fake call on OBS API")

        return ConsumptionOfDevice("pipo", 3145728, 2411724, 1234, 1234)

        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            # async with async_timeout.timeout(10):
            # Grab active context variables to limit data required to be fetched from API
            # Note: using context is not required if there is no need or ability to limit
            # data retrieved from API.
            # listening_idx = set(self.async_contexts())
            # return await self.my_api.fetch_data(listening_idx)

            """
            auth_token = await self.obs_api_client.get_auth_token()
            user_info = await self.obs_api_client.get_user_info()
            first_device_info = await self.obs_api_client.get_devices_info()
            consumption_info = await self.obs_api_client.get_consumption_of_device(device=first_device_info)

            return consumption_info
            """
        except ApiAuthError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err
        except ApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
