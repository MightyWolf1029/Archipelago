from .OoTR.Dungeon import *

def __init__(self, world, name, hint, font_color, boss_key=None, small_keys=None, dungeon_items=None):
    """
    Modified implementation of `Dungeon`'s `__init__` function.
    Uses the regions from multiworld and checks the player before
    populating the regions
    """

    self.world = world
    self.name = name
    self.hint_text = hint
    self.font_color = font_color
    self.regions = []
    self.boss_key = boss_key if boss_key is not None else []
    self.small_keys = small_keys if small_keys is not None else []
    self.dungeon_items = dungeon_items if dungeon_items is not None else []

    for region in world.multiworld.regions:
        if region.player == world.player and region.dungeon == self.name:
            region.dungeon = self
            self.regions.append(region)

# Patch OoTR's Dungeon class with our modified __init__ function
Dungeon.__init__ = __init__
