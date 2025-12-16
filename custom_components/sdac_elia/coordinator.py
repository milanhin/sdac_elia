import logging
import datetime
import requests
import aiohttp

from typing import Any
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.typing import ConfigType
from homeassistant.core import HomeAssistant
from homeassistant import config_entries

from .const import (
    CONF_PRICE_FACTOR,
    CONF_FIXED_PRICE,
    CONF_FIXED_INJ_PRICE,
    CONF_INJ_TARIFF_FACTOR,
    PRICES,
    CURRENT_PRICE,
    LAST_FETCH_TIME,
)

_LOGGER = logging.getLogger(__name__)

class SDAC_EliaCoordinator(DataUpdateCoordinator):
    def __init__(
            self,
            hass: HomeAssistant,
            platform_config: ConfigType,
            custom_price_configured: bool,
            custom_inj_configured: bool,
            custom_params: dict[str, float],
    ) -> None:
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name="SDAC_Elia-coordinator",
            config_entry=None,
            update_interval=datetime.timedelta(minutes=1)               # Interval for which to update coordinator data
        )
        self.custom_price_configured = custom_price_configured
        self.custom_inj_configured = custom_inj_configured

        self.last_fetch_today: datetime.datetime | None = None          # Time of last data fetch for today
        self.last_fetch_date: datetime.date | None = None               # Date of last data fetch for today
        self.last_fetch_tmrw: datetime.datetime | None = None           # Time of last data fetch for tomorrow
        self.last_fetch_time: datetime.datetime | None = None           # Last time of fetching
        self.fetched_tomorrow: bool = False                             # Bool for fetched prices of tomorrow
        self.prices: list[dict] = []                                    # Filtered data with time and price pairs of today and tomorrow
        self.sdac_price: float | None = None                            # Current SDAC price
        self.ecopower_price: float | None = None                        # Current electricity price for Ecopower clients
        self.ecopower_inj_tariff: float | None = None                   # Current injection tariff for Ecopower clients
        self.custom_price: float | None = None                          # Price based on config formula
        self.custom_inj_tariff: float | None = None                     # Injection tariff based on config formula
        
        if self.custom_price_configured:
            self.conf_price_factor: float = custom_params[CONF_PRICE_FACTOR]            # Factor of EPEX for price formula
            self.conf_fixed_price: float = custom_params[CONF_FIXED_PRICE]              # Fixed added price for price formula
        if self.custom_inj_configured:
            self.conf_rel_inj_tariff: float = custom_params[CONF_INJ_TARIFF_FACTOR]     # Factor of EPEX for injection tariff formula
            self.conf_fixed_inj_price: float = custom_params[CONF_FIXED_INJ_PRICE]      # Fixed added price for injection tariff formula
    
    async def _async_setup(self):
        _LOGGER.info("SDAC_Elia coordinator was set up")

    async def _async_update_data(self) -> dict[str, Any]:
        time_now = datetime.datetime.now()
        date_today = datetime.date.today()
        date_tomorrow = date_today + datetime.timedelta(days=1)

        # Fetch prices of today
        if self.last_fetch_date != date_today:
            self.prices = []  # Empty price list on new day
            self.fetched_tomorrow = False
            try:
                sdac_today = await self._fetch_data(date_today)
            except Exception as err:
                _LOGGER.error("Error fetching data from Elia: %s", err)
                return self.data
            
            if len(sdac_today):  # If prices haven't been publsihed yet, an empty list will be returned
                _LOGGER.info("SDAC prices of today fetched from Elia")
                self.prices = [{"time": i["dateTime"], "price": i["price"]} for i in sdac_today]  # filter data to store time and price
                self.last_fetch_today = time_now
                self.last_fetch_date = date_today

        # Fetch prices of tomorrow
        if not self.fetched_tomorrow and time_now.hour >= 13:
            if self.last_fetch_tmrw == None or self.last_fetch_tmrw - time_now > datetime.timedelta(minutes=10):
                try:
                    sdac_tomorrow = await self._fetch_data(date_tomorrow)
                    self.last_fetch_tmrw = time_now
                except Exception as err:
                    _LOGGER.error("Error fetching data from Elia: %s", err)
                    return self.data
                
                if len(sdac_tomorrow):  # If prices haven't been published yet, an empty list will be returned
                    _LOGGER.info("SDAC prices of tomorrow fetched from Elia")
                    prices_tomorrow = [{"time": i["dateTime"], "price": i["price"]} for i in sdac_tomorrow]  # filter data to store time and price
                    self.prices.extend(prices_tomorrow)
                    self.fetched_tomorrow = True
        
        # Grab and calculate prices for sensors
        self.sdac_price = self.get_current_price()  # Find current price
        if self.sdac_price != None:
            self.ecopower_price = self.calculate_ecopower_price(sdac=self.sdac_price)
            self.ecopower_inj_tariff = self.calculate_ecopower_inj_tariff(sdac=self.sdac_price)
            
            if self.custom_price_configured:
                self.custom_price = self.calculate_custom_price(sdac=self.sdac_price)
            if self.custom_inj_configured:
                self.custom_inj_tariff = self.calculate_custom_inj_tariff(sdac=self.sdac_price)

        self.last_fetch_time = self.last_fetch_tmrw if self.fetched_tomorrow else self.last_fetch_today
        data = {
            PRICES: self.prices,
            CURRENT_PRICE: self.sdac_price,
            LAST_FETCH_TIME: self.last_fetch_time
        }
        return data
    
    async def _fetch_data(self, date) -> Any:
        time_now = datetime.datetime.now()
        url = f"https://griddata.elia.be/eliabecontrols.prod/interface/Interconnections/daily/auctionresultsqh/{date}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                payload = await resp.json()
                return payload
    
    def get_current_price(self) -> float | None:
        if not len(self.prices):
            return None
        
        utc_time = datetime.datetime.now(datetime.timezone.utc)                                     # Get current UTC time
        rounded_quarter = utc_time.minute // 15 * 15                                                # determine last quarter minutes
        rounded_utc_time = utc_time.replace(microsecond=0, second=0, minute=rounded_quarter)        # change current minutes to last quarter
        target_time_str = rounded_utc_time.strftime("%Y-%m-%dT%H:%M:%SZ")                           # Create string to match standard
        current_price_dict = next((p for p in self.prices if p["time"] == target_time_str), None)   # Get time matching price dict
        if current_price_dict == None:
            _LOGGER.error("No time match found in prices from Elia")
            return None
        current_price = current_price_dict["price"]
        return current_price
    
    def calculate_ecopower_price(self, sdac: float) -> float:
        rounded_price = round(1.02 * sdac + 4, 2)
        return rounded_price
    
    def calculate_ecopower_inj_tariff(self, sdac: float) -> float:
        rounded_inj_tariff = round(0.98 * sdac - 15, 2)
        return rounded_inj_tariff
    
    def calculate_custom_price(self, sdac: float) -> float:
        custom_price = (self.conf_price_factor * sdac + self.conf_fixed_price) * 1e3
        rounded_custom_price = round(custom_price, 2)
        return rounded_custom_price
    
    def calculate_custom_inj_tariff(self, sdac: float) -> float:
        custum_inj_tariff = (self.conf_rel_inj_tariff * sdac - self.conf_fixed_inj_price) * 1e3
        rounded_custom_inj_tariff = round(custum_inj_tariff, 2)
        return rounded_custom_inj_tariff