from .OoTR.Messages import *
from .OoTR import Messages as OoTRMessages

# Add the Archipelago item messages
ITEM_MESSAGES[0x9097] = "\x08You got an \x05\x41Archipelago item\x05\x40!\x01It seems \x05\x41important\x05\x40!"
ITEM_MESSAGES[0x9098] = "\x08You got an \x05\x43Archipelago item\x05\x40!\x01Doesn't seem like it's needed."

# reduce item message sizes and add new item messages
# make sure to call this AFTER move_shop_item_messages()
def update_item_messages(messages, world):
    """
    Modified implementation of `Messages`'s `update_item_messages` function.
    Checks the number of players in the multiworld instead of the world count
    in settings.
    """
    new_item_messages = {**ITEM_MESSAGES, **KEYSANITY_MESSAGES}
    for id, text in new_item_messages.items():
        if world.multiworld.players > 1:
            update_message_by_id(messages, id, make_player_message(text), 0x23)
        else:
            update_message_by_id(messages, id, text, 0x23)

    for id, (text, opt) in MISC_MESSAGES.items():
        update_message_by_id(messages, id, text, opt)

# shuffles the messages in the game, making sure to keep various message types in their own group
def shuffle_messages(messages, rand, except_hints=True, always_allow_skip=True):
    """
    Modified implementation of `Messages`'s `shuffle_messages` function. Uses the world's
    rand object instead of Python's random.
    """
    permutation = [i for i, _ in enumerate(messages)]

    def is_exempt(m):
        hint_ids = (
            GOSSIP_STONE_MESSAGES + TEMPLE_HINTS_MESSAGES +
            [data['id'] for data in misc_item_hint_table.values()] +
            [data['id'] for data in misc_location_hint_table.values()] +
            list(KEYSANITY_MESSAGES.keys()) + shuffle_messages.shop_item_messages +
            shuffle_messages.scrubs_message_ids +
            [0x5036, 0x70F5] # Chicken count and poe count respectively
        )
        shuffle_exempt = [
            0x208D,         # "One more lap!" for Cow in House race.
        ]
        is_hint = (except_hints and m.id in hint_ids)
        is_error_message = (m.id == ERROR_MESSAGE)
        is_shuffle_exempt = (m.id in shuffle_exempt)
        return (is_hint or is_error_message or m.is_id_message() or is_shuffle_exempt)

    have_goto         = list( filter(lambda m: not is_exempt(m) and m.has_goto,         messages) )
    have_keep_open    = list( filter(lambda m: not is_exempt(m) and m.has_keep_open,    messages) )
    have_event        = list( filter(lambda m: not is_exempt(m) and m.has_event,        messages) )
    have_fade         = list( filter(lambda m: not is_exempt(m) and m.has_fade,         messages) )
    have_ocarina      = list( filter(lambda m: not is_exempt(m) and m.has_ocarina,      messages) )
    have_two_choice   = list( filter(lambda m: not is_exempt(m) and m.has_two_choice,   messages) )
    have_three_choice = list( filter(lambda m: not is_exempt(m) and m.has_three_choice, messages) )
    basic_messages    = list( filter(lambda m: not is_exempt(m) and m.is_basic(),       messages) )


    def shuffle_group(group):
        group_permutation = [i for i, _ in enumerate(group)]
        rand.shuffle(group_permutation)

        for index_from, index_to in enumerate(group_permutation):
            permutation[group[index_to].index] = group[index_from].index

    # need to use 'list' to force 'map' to actually run through
    list( map( shuffle_group, [
        have_goto + have_keep_open + have_event + have_fade + basic_messages,
        have_ocarina,
        have_two_choice,
        have_three_choice,
    ]))

    return permutation

# Update warp song text boxes for ER
def update_warp_song_text(messages, world):
    """
    Modified implementation of `Messages`'s `update_warp_song_text` function. Correctly
    access the world's `logic_rules`, `misc_hints`, and `warp_songs`.
    """
    from .OoTR.Hints import HintArea

    msg_list = {
        0x088D: 'Minuet of Forest Warp -> Sacred Forest Meadow',
        0x088E: 'Bolero of Fire Warp -> DMC Central Local',
        0x088F: 'Serenade of Water Warp -> Lake Hylia',
        0x0890: 'Requiem of Spirit Warp -> Desert Colossus',
        0x0891: 'Nocturne of Shadow Warp -> Graveyard Warp Pad Region',
        0x0892: 'Prelude of Light Warp -> Temple of Time',
    }

    if world.logic_rules != "glitched": # Entrances not set on glitched logic so following code will error
        for id, entr in msg_list.items():
            if 'warp_songs' in world.misc_hints or not world.warp_songs:
                destination = world.get_entrance(entr).connected_region
                destination_name = HintArea.at(destination)
                color = COLOR_MAP[destination_name.color]
                if destination_name.preposition(True) is not None:
                    destination_name = f'to {destination_name}'
            else:
                destination_name = 'to a mysterious place'
                color = COLOR_MAP['White']

            new_msg = f"\x08\x05{color}Warp {destination_name}?\x05\40\x09\x01\x01\x1b\x05\x42OK\x01No\x05\40"
            update_message_by_id(messages, id, new_msg)

# Patch OoTR's Messages functions with our modified functions
OoTRMessages.update_item_messages = update_item_messages
OoTRMessages.shuffle_messages = shuffle_messages
OoTRMessages.update_warp_song_text = update_warp_song_text
