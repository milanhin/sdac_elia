from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import(
    DOMAIN,
    CONFIG,
)

async def async_setup_entry(
    hass: HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry"""

    platform_config = {**entry.data, **entry.options}
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][CONFIG] = platform_config

    # Forward setup to sensor platform
    await hass.config_entries.async_forward_entry_setups(entry=entry, platforms=["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Unload platform after reconfigure through OptionsFlow"""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    return unload_ok