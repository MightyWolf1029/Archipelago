from .OoTR.LocationList import *

# relevant for both dungeon item fill and song fill
dungeon_song_locations = [
    "Deku Tree Queen Gohma Heart",
    "Dodongos Cavern King Dodongo Heart",
    "Jabu Jabus Belly Barinade Heart",
    "Forest Temple Phantom Ganon Heart",
    "Fire Temple Volvagia Heart",
    "Water Temple Morpha Heart",
    "Shadow Temple Bongo Bongo Heart",
    "Spirit Temple Twinrova Heart",
    "Song from Impa",
    "Sheik in Ice Cavern",
    # only one exists
    "Bottom of the Well Lens of Truth Chest", "Bottom of the Well MQ Lens of Truth Chest",
    # only one exists
    "Gerudo Training Ground Maze Path Final Chest", "Gerudo Training Ground MQ Ice Arrows Chest",
]

# This function has moved to World.py in later versions of OoTR
def set_drop_location_names(ootworld):
    """
    Function to run exactly once after after placing items in drop locations for each world
    Sets all Drop locations to a unique name in order to avoid name issues and to identify locations in the spoiler
    Also cause them to not be shown in the list of locations, only in playthrough
    """
    for region in ootworld.regions:
        for location in region.locations:
            if location.type == 'Drop':
                location.name = location.parent_region.name + " " + location.name
                location.show_in_spoiler = False
