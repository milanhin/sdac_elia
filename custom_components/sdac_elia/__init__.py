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
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][CONFIG] = entry.data

    # Forward setup to sensor platform
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry=entry, platforms=["sensor"])
    )
    return True