from BaseClasses import Item as APItem, ItemClassification
from .OoTR.Item import Item as OoTRItem, ItemInfo
from .OoTR.ItemList import item_table

def oot_data_to_ap_id(data, event):
    """
    Custom AP helper function.
    """
    if event or data[2] is None or data[0] == 'Shop':
        return None
    offset = 66000
    if data[0] in ['Item', 'BossKey', 'Compass', 'Map', 'SmallKey', 'Token', 'GanonBossKey', 'HideoutSmallKey', 'Song']:
        return offset + data[2]
    else:
        raise Exception(f'Unexpected OOT item type found: {data[0]}')

def ap_id_to_oot_data(ap_id):
    """
    Custom AP helper function.
    """
    offset = 66000
    val = ap_id - offset
    try:
        return list(filter(lambda d: d[1][0] == 'Item' and d[1][2] == val, item_table.items()))[0]
    except IndexError:
        raise Exception(f'Could not find desired item ID: {ap_id}')

def oot_is_item_of_type(item, item_type):
    """
    Custom AP helper function. Checks if ``item`` is of type ``item_type``.
    Args:
        item: An ``OOTItem`` or ``str`` to check
        item_type: The expected item type as a ``str``

    Returns:
        True if the provided ``item``'s type matches ``item_type``, False otherwise
    """
    if isinstance(item, OOTItem):
        return item.type == item_type
    if isinstance(item, str):
        return item in item_table and item_table[item][0] == item_type
    return False

class OOTItem(APItem, OoTRItem):
    """
    A class to represent an item in OoT. Inherits from AP's base ``Item`` class as well as OoTR's ``Item`` class.
    """
    game: str = "Ocarina of Time"
    type: str

    def __init__(self, name, player, event, force_not_advancement):
        # We can't call the OoTRItem's __init__ due to the advancement attribute conflicting with one of APItem's
        # properties. Create an attribute that is an OoTRItem to get around it.
        self.ootrItem = OoTRItem(name, None, event)
        if event:
            data = ('Event', True, None, None)
        else:
            data = item_table[name]
        # "advancement" is True, False or None; some items are not advancement based on settings
        if force_not_advancement:
            classification = ItemClassification.useful
        elif name == "Ice Trap":
            classification = ItemClassification.trap
        elif name in {'Gold Skulltula Token', 'Triforce Piece'}:
            classification = ItemClassification.progression_skip_balancing
        elif self.ootrItem.advancement:
            classification = ItemClassification.progression
        else:
            classification = ItemClassification.filler
        APItem.__init__(self, name, classification, oot_data_to_ap_id(data, event), player)
        # These attributes are set in OoTRItem
        self.type = self.ootrItem.type
        self.index = self.ootrItem.index
        self.special = self.ootrItem.special
        # These attributes are unique to this class
        self.price = self.special.get('price', None) if self.special else None
        self.internal = False
