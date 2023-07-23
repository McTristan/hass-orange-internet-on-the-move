"""Platform for sensor integration."""
from __future__ import annotations

import logging
from datetime import timedelta, datetime
from math import floor

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfInformation, PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity, UpdateFailed

from .dto import ConsumptionOfDevice, Device, OBSFullData
from .OBSHttpClient import ObsHttpClient, ApiAuthError
from .const import (
    DOMAIN, ENDPOINT_HEADER_PROVIDER, )

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
    new_devices = [
        SensorDataBase(obs_coordinator, obs_coordinator.data),
        StartDatePlanSensorEntity(obs_coordinator, obs_coordinator.data),
        ExpiryDatePlanSensorEntity(obs_coordinator, obs_coordinator.data),
        DataInitialSensorEntity(obs_coordinator, obs_coordinator.data),
        DataLeftSensorEntity(obs_coordinator, obs_coordinator.data),
        DataLeftPercentageSensorEntity(obs_coordinator, obs_coordinator.data),
        PlanTypeSensorEntity(obs_coordinator, obs_coordinator.data)
    ]
    _LOGGER.info(f"async_add_entities new_devices={new_devices}")
    if new_devices:
        async_add_entities(new_devices)
    _LOGGER.info("async_add_entities done")


class SensorDataBase(CoordinatorEntity):
    def __init__(self, coordinator, obs_full_data: OBSFullData):
        """Initialize the sensor."""
        super().__init__(coordinator, context=obs_full_data)
        self.device_consumption = obs_full_data.consumption
        self.device = obs_full_data.device
        self.id = self.device.device_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        # return {"identifiers": {(DOMAIN, self.id)}}
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.id)
            },
            name=f"Data Plan of {self.device.user_name} for {self.device.tag}",
            manufacturer=f"Orange for {ENDPOINT_HEADER_PROVIDER}",
            model=self.device.tag,
            hw_version=self.device.serial_number
        )


class DataLeftPercentageSensorEntity(SensorEntity, SensorDataBase):

    def __init__(self, coordinator, obs_full_data: OBSFullData):
        _LOGGER.info(f"Creating DataSensorEntity with {obs_full_data}")
        """Pass coordinator to CoordinatorEntity."""

        super().__init__(coordinator, obs_full_data)
        self._attr_name = "Left data percentage"
        self._attr_unique_id = f"{self.id}_left_data_percentage"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_icon = "mdi:gauge"
        self._attr_native_value = floor(
            obs_full_data.consumption.left_data / obs_full_data.consumption.initial_data * 100)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        new_state_value = floor(
            self.coordinator.data.consumption.left_data / self.coordinator.data.consumption.initial_data * 100)
        _LOGGER.info(
            f"DataConsumedSensorEntity _handle_coordinator_update previous : {self._attr_native_value} new {new_state_value}")
        self._attr_native_value = new_state_value
        self.async_write_ha_state()


class DataLeftSensorEntity(SensorEntity, SensorDataBase):

    def __init__(self, coordinator, obs_full_data: OBSFullData):
        _LOGGER.info(f"Creating DataLeftSensorEntity with {obs_full_data}")
        super().__init__(coordinator, obs_full_data)
        self._attr_name = "Left data"
        self._attr_unique_id = f"{self.id}_left_data"
        self._attr_native_unit_of_measurement = UnitOfInformation.MEGABYTES
        self._attr_device_class = SensorDeviceClass.DATA_SIZE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_value = obs_full_data.consumption.left_data / 1024

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        new_state_value = self.coordinator.data.consumption.left_data / 1024
        _LOGGER.info(
            f"DataConsumedSensorEntity _handle_coordinator_update previous : {self._attr_native_value} new {new_state_value}")
        self._attr_native_value = new_state_value
        self.async_write_ha_state()


class DataInitialSensorEntity(SensorEntity, SensorDataBase):

    def __init__(self, coordinator, obs_full_data: OBSFullData):
        _LOGGER.info(f"Creating DataSensorEntity with {obs_full_data}")
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, obs_full_data)
        self._attr_name = "Initial Data"
        self._attr_unique_id = f"{self.id}_initial_data"
        self._attr_native_unit_of_measurement = UnitOfInformation.MEGABYTES
        self._attr_device_class = SensorDeviceClass.DATA_SIZE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_value = obs_full_data.consumption.initial_data / 1024

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        new_state_value = self.coordinator.data.consumption.initial_data / 1024
        _LOGGER.info(
            f"DataSensorEntity _handle_coordinator_update previous : {self._attr_native_value} new {new_state_value}")
        self._attr_native_value = new_state_value
        self.async_write_ha_state()


class StartDatePlanSensorEntity(SensorEntity, SensorDataBase):

    def __init__(self, coordinator, obs_full_data: OBSFullData):
        _LOGGER.info(f"Creating DatePlanSensorEntity with {obs_full_data}")
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, obs_full_data)
        self._attr_name = "Start date"
        self._attr_unique_id = f"{self.id}_start_date"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_native_value = datetime.fromisoformat(obs_full_data.consumption.start_date)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        new_state_value = datetime.fromisoformat(self.coordinator.data.consumption.start_date)
        _LOGGER.info(
            f"StartDatePlanSensorEntity _handle_coordinator_update previous : {self._attr_native_value} new {new_state_value}")
        self._attr_native_value = new_state_value
        self.async_write_ha_state()


class ExpiryDatePlanSensorEntity(SensorEntity, SensorDataBase):

    def __init__(self, coordinator, obs_full_data: OBSFullData):
        _LOGGER.info(f"Creating DatePlanSensorEntity with {obs_full_data}")
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, obs_full_data)
        self._attr_name = "Expiry date"
        self._attr_unique_id = f"{self.id}_expiry_date"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_native_value = datetime.fromisoformat(obs_full_data.consumption.expiry_date)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        new_state_value = datetime.fromisoformat(self.coordinator.data.consumption.expiry_date)
        _LOGGER.info(
            f"ExpiryDatePlanSensorEntity _handle_coordinator_update previous : {self._attr_native_value} new {new_state_value}")
        self._attr_native_value = new_state_value
        self.async_write_ha_state()


class PlanTypeSensorEntity(SensorEntity, SensorDataBase):

    def __init__(self, coordinator, obs_full_data: OBSFullData):
        _LOGGER.info(f"Creating DatePlanSensorEntity with {obs_full_data}")
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, obs_full_data)
        self._attr_name = "Plan Type"
        self._attr_unique_id = f"{self.id}_plan_type"
        self._attr_native_value = obs_full_data.consumption.type
        self._attr_icon = "mdi:file-sign"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        new_state_value = self.coordinator.data.consumption.type
        _LOGGER.info(
            f"PlanTypeSensorEntity _handle_coordinator_update previous : {self._attr_native_value} new {new_state_value}")
        self._attr_native_value = new_state_value
        self.async_write_ha_state()


class OBSCoordinator(DataUpdateCoordinator[OBSFullData]):
    """A coordinator to fetch data from the api only once"""

    def __init__(self, hass, obs_api_client: ObsHttpClient):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Orange Internet on the move sensor",
            update_interval=timedelta(seconds=3600),
        )
        self.obs_api_client: ObsHttpClient = obs_api_client

    async def _async_update_data(self) -> OBSFullData:
        _LOGGER.debug("Starting collecting data")

        # return ConsumptionOfDevice("pipo", 3145728, 2411724, 1234, 1234)

        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            await self.obs_api_client.authenticate_and_store_token()
            first_device: Device = await self.obs_api_client.get_first_device_info()
            _LOGGER.debug(f"First device fetched : {first_device}")
            consumption_info: ConsumptionOfDevice = \
                await self.obs_api_client.get_consumption_of_device(device=first_device)
            _LOGGER.debug(f"Consumption fetched : {consumption_info}")

            return OBSFullData(device=first_device, consumption=consumption_info)
        except ApiAuthError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err
        # except ApiError as err:
        #     raise UpdateFailed(f"Error communicating with API: {err}")
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
