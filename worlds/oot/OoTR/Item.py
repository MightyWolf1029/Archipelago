import typing

from BaseClasses import Item, ItemClassification

from .ItemList import item_table

def oot_data_to_ap_id(data, event): 
    if event or data[2] is None or data[0] == 'Shop': 
        return None
    offset = 66000
    if data[0] in ['Item', 'BossKey', 'Compass', 'Map', 'SmallKey', 'Token', 'GanonBossKey', 'HideoutSmallKey', 'Song']:
        return offset + data[2]
    else: 
        raise Exception(f'Unexpected OOT item type found: {data[0]}')


def ap_id_to_oot_data(ap_id): 
    offset = 66000
    val = ap_id - offset
    try: 
        return list(filter(lambda d: d[1][0] == 'Item' and d[1][2] == val, item_table.items()))[0]
    except IndexError: 
        raise Exception(f'Could not find desired item ID: {ap_id}')


def oot_is_item_of_type(item, item_type):
    if isinstance(item, OOTItem):
        return item.type == item_type
    if isinstance(item, str):
        return item in item_table and item_table[item][0] == item_type
    return False


class OOTItem(Item):
    game: str = "Ocarina of Time"
    type: str

    def __init__(self, name, player, data, event, force_not_advancement):
        (type, advancement, index, special) = data
        # "advancement" is True, False or None; some items are not advancement based on settings
        if force_not_advancement:
            classification = ItemClassification.useful
        elif name == "Ice Trap":
            classification = ItemClassification.trap
        elif name in {'Gold Skulltula Token', 'Triforce Piece'}:
            classification = ItemClassification.progression_skip_balancing
        elif advancement:
            classification = ItemClassification.progression
        else:
            classification = ItemClassification.filler
        super(OOTItem, self).__init__(name, classification, oot_data_to_ap_id(data, event), player)
        self.type = type
        self.index = index
        self.special = special or {}
        self.price = special.get('price', None) if special else None
        self.internal = False

    @property
    def dungeonitem(self) -> bool:
        return self.type in ['SmallKey', 'HideoutSmallKey', 'BossKey', 'GanonBossKey', 'Map', 'Compass']
