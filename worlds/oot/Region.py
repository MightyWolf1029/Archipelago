from BaseClasses import Region as APRegion, MultiWorld
from .OoTR.Hints import HintArea
from .OoTR.Region import Region as OoTRRegion, TimeOfDay

class OOTRegion(APRegion, OoTRRegion):
    """
    A class to represent a region in OoT. Inherits from AP's base ``Region`` class as well as
    OoTR's ``Region``.
    """
    game: str = "Ocarina of Time"

    def __init__(self, name: str, player: int, multiworld: MultiWorld):
        APRegion.__init__(self, name, player, multiworld)
        OoTRRegion.__init__(self, name, None) # AP doesn't use OoTRRegion's type property
        self._oot_hint = None
        self._alt_hint = None
        self.dungeon = None
        self.pretty_name = None
        self.font_color = None

    # This is too generic of a name to risk not breaking in the future.
    # This lets us possibly switch it out later if AP starts using it.
    @property
    def hint(self):
        return self._oot_hint

    @hint.setter
    def hint(self, value):
        self._oot_hint = value

    @property
    def alt_hint(self):
        return self._alt_hint

    @alt_hint.setter
    def alt_hint(self, value):
        self._alt_hint = value

    def can_reach(self, state):
        """
        A helper function to determine if this ``OOTRegion`` can be reached.
        Args:
            state: The current state
        Returns:
            ``True`` if this ``OOTRegion`` can be reached, ``False`` otherwise
        """
        if state._oot_stale[self.player]:
            stored_age = state.age[self.player]
            state._oot_update_age_reachable_regions(self.player)
            state.age[self.player] = stored_age
        if state.age[self.player] == 'child':
            return self in state.child_reachable_regions[self.player]
        elif state.age[self.player] == 'adult':
            return self in state.adult_reachable_regions[self.player]
        else: # we don't care about age
            return self in state.child_reachable_regions[self.player] or self in state.adult_reachable_regions[self.player]

    def set_hint_data(self, hint):
        """
        A helper function to set this ``OOTRegion``'s hint data.
        Args:
            hint: The hint data to set.
        """
        if self.dungeon:
            self._oot_hint = HintArea.for_dungeon(self.dungeon)
        else:
            self._oot_hint = HintArea[hint]
        self._hint_text = str(self._oot_hint)
