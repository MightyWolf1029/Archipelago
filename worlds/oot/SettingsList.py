# The only thing we need from this file is the list of all logic tricks
from .OoTR.SettingsList import logic_tricks as known_logic_tricks

normalized_name_tricks = {trick.casefold(): info for (trick, info) in known_logic_tricks.items()}
