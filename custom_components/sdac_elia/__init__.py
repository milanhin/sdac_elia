from homeassistant import config_entries
from homeassistant.core import HomeAssistant

async def async_setup_entry(
    hass: HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    
    return True