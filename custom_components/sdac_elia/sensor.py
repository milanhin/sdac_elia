"""Platform for sensor integration."""
from __future__ import annotations
import datetime
import requests
import logging
import voluptuous as vol

from typing import Any
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    PLATFORM_SCHEMA
)
from homeassistant import config_entries
from homeassistant.const import CURRENCY_EURO
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import SDAC_EliaCoordinator
from .const import(
    CONF_FIXED_PRICE,
    CONF_PRICE_FACTOR,
    CONF_FIXED_INJ_PRICE,
    CONF_INJ_TARIFF_FACTOR,
    CONF_CUSTOM_INJ_TARIFF,
    CONF_CUSTOM_PRICE,
    PRICES,
    CURRENT_PRICE,
    LAST_FETCH_TIME,
    DOMAIN,
    CONFIG,
    CONF_USER_STEP,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: config_entries.ConfigEntry,
        async_add_entities,
):
    """Set up sensor from config entry"""
    config = hass.data[DOMAIN][CONFIG]

    # Check if custom formulae are configured
    custom_price_configured: bool = False
    custom_inj_configured: bool = False
    custom_params: dict[str, float] = {}

    # Check if custom price is configured and put coefficients in dict
    if config[CONF_USER_STEP][CONF_CUSTOM_PRICE]:
        custom_price_configured = True
        custom_params[CONF_PRICE_FACTOR] = config[CONF_CUSTOM_PRICE][CONF_PRICE_FACTOR]
        custom_params[CONF_FIXED_PRICE] = config[CONF_CUSTOM_PRICE][CONF_FIXED_PRICE]

    # Check if custom injection tariff is configured and put coefficients in dict
    if config[CONF_USER_STEP][CONF_CUSTOM_INJ_TARIFF]:
        custom_inj_configured = True
        custom_params[CONF_INJ_TARIFF_FACTOR] = config[CONF_CUSTOM_INJ_TARIFF][CONF_INJ_TARIFF_FACTOR]
        custom_params[CONF_FIXED_INJ_PRICE] = config[CONF_CUSTOM_INJ_TARIFF][CONF_FIXED_INJ_PRICE]

    # Initialise coordinator
    sdac_coordinator = SDAC_EliaCoordinator(
        hass=hass,
        platform_config=config,
        custom_price_configured=custom_price_configured,
        custom_inj_configured=custom_inj_configured,
        custom_params=custom_params,
    )

    await sdac_coordinator.async_refresh()  # Call _async_update_data() on setup
    entities_to_add = [
        EliaSensor(sdac_coordinator),
        EcopowerPriceSensor(sdac_coordinator),
        EcopowerInjectionSensor(sdac_coordinator),
    ]

    if custom_price_configured:
        entities_to_add.append(CustomPriceSensor(sdac_coordinator))         # Add sensor if configured
    if custom_inj_configured:
        entities_to_add.append(CustomInjectionSensor(sdac_coordinator))     # Add sensor if configured

    async_add_entities(entities_to_add)
    _LOGGER.info("SDAC_Elia platform was set up")

class EliaSensor(CoordinatorEntity, SensorEntity): # pyright: ignore[reportIncompatibleVariableOverride]
    """Representation of a Sensor."""

    _attr_name = "Elia SDAC current price"                      # Name of sensor
    _attr_native_unit_of_measurement = f"{CURRENCY_EURO}/MWh"   # Unit of state value
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: SDAC_EliaCoordinator) -> None:
        super().__init__(coordinator)
        self.coordinator = coordinator
    
    @property
    def native_value(self) -> float | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return the current SDAC price so it gets stored in the sensor as value"""
        return self.coordinator.data[CURRENT_PRICE]
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]: # pyright: ignore[reportIncompatibleVariableOverride]
        """Store all SDAC prices of the day."""
        return {
            "Last update:": self.coordinator.data[LAST_FETCH_TIME],
            "prices": self.coordinator.data[PRICES],
            }


class EcopowerPriceSensor(CoordinatorEntity, SensorEntity): # pyright: ignore[reportIncompatibleVariableOverride]
    """Sensor to show current electricity price for Ecopower clients"""
    _attr_name = "Ecopower electricity price"                   # Name of sensor
    _attr_native_unit_of_measurement = f"{CURRENCY_EURO}/MWh"   # Unit of state value
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: SDAC_EliaCoordinator) -> None:
        super().__init__(coordinator)
        self.coordinator = coordinator
    
    @property
    def native_value(self) -> float | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return Ecopower electricity price so it gets stored in the sensor as value"""
        return self.coordinator.ecopower_price


class EcopowerInjectionSensor(CoordinatorEntity, SensorEntity): # pyright: ignore[reportIncompatibleVariableOverride]
    """Sensor to show current injection tariff for Ecopower clients"""
    _attr_name = "Ecopower injection tariff"                      # Name of sensor
    _attr_native_unit_of_measurement = f"{CURRENCY_EURO}/MWh"   # Unit of state value
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: SDAC_EliaCoordinator) -> None:
        super().__init__(coordinator)
        self.coordinator = coordinator
    
    @property
    def native_value(self) -> float | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return Ecopower injection tariff so it gets stored in the sensor as value"""
        return self.coordinator.ecopower_inj_tariff


class CustomPriceSensor(CoordinatorEntity, SensorEntity): # pyright: ignore[reportIncompatibleVariableOverride]
    """Sensor to show current price based on config formula"""
    _attr_name = "Custom electricity price"                         # Name of sensor
    _attr_native_unit_of_measurement = f"{CURRENCY_EURO}/MWh"       # Unit of state value
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: SDAC_EliaCoordinator) -> None:
        super().__init__(coordinator)
        self.coordinator = coordinator
    
    @property
    def native_value(self) -> float | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return custom price based on parameters in yaml config"""
        return self.coordinator.custom_price


class CustomInjectionSensor(CoordinatorEntity, SensorEntity): # pyright: ignore[reportIncompatibleVariableOverride]
    """Sensor to show current injection tariff based on custom config formula"""
    _attr_name = "Custom injection tariff"                        # Name of sensor
    _attr_native_unit_of_measurement = f"{CURRENCY_EURO}/MWh"   # Unit of state value
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: SDAC_EliaCoordinator) -> None:
        super().__init__(coordinator)
        self.coordinator = coordinator
    
    @property
    def native_value(self) -> float | None: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return custom injection tariff based on parameters in yaml config"""
        return self.coordinator.custom_inj_tariff