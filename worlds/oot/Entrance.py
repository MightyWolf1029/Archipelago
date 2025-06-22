from BaseClasses import Entrance as APEntrance
from .OoTR.Entrance import Entrance as OoTREntrance

class OOTEntrance(APEntrance, OoTREntrance):
    """
    A class to represent an entrance in OoT. Inherits from AP's base ``Entrance`` class as well as
    OoTR's ``Entrance``.
    """
    game: str = 'Ocarina of Time'

    def __init__(self, player, multiworld, name='', parent=None):
        APEntrance.__init__(self, player, name, parent)
        self.multiworld = multiworld
        self.access_rules = []
        self.reverse = None
        self.replaces = None
        self.assumed = None
        self.type = None
        self.shuffled = False
        self.data = None
        self.primary = False
        self.always = False
        self.never = False

    def get_new_target(self, pool_type):
        """
        Modified implementation of OoTREntrance's ``get_new_target``. It accepts an additional argument ``pool_type``
        and utilizes the ``multiworld`` and ``player`` members when creating the ``OOTEntrance`` instance.
        """
        ########################
        # Begin AP modified code
        root = self.multiworld.get_region('Root Exits', self.player)
        target_entrance = OOTEntrance(self.player, self.multiworld, f'Root -> ({self.name}) ({pool_type})', root)
        # End AP modified code
        ########################
        target_entrance.connect(self.connected_region)
        target_entrance.replaces = self
        root.exits.append(target_entrance)
        return target_entrance

    def assume_reachable(self, pool_type):
        """
        Modified implementation of OoTREntrance's ``assume_reachable``. It accepts an additional argument ``pool_type``
        which is used when calling the modified version of ``get_new_target``.
        """
        if self.assumed == None:
            ########################
            # Begin AP modified code
            self.assumed = self.get_new_target(pool_type)
            # End AP modified code
            ########################
            self.disconnect()
        return self.assumed
