import typing

from test.bases import WorldTestBase
from ..Options import open_options, world_options, bridge_options, shuffle_options, dungeon_items_options, timesavers_options, \
    misc_options, itempool_options, cosmetic_options, sfx_options

class OOTTestBase(WorldTestBase):
    game = "Ocarina of Time"

def all_options() -> typing.Dict[str, typing.Any]:
    """Return a single dict containing all the options"""
    return open_options | world_options | bridge_options | shuffle_options | dungeon_items_options | timesavers_options \
        | misc_options | itempool_options | cosmetic_options | sfx_options

def max_shuffle() -> typing.Dict[str, typing.Any]:
    """Turn up all shuffle settings so all items are added to the item pool"""
    options = {}
    options["shuffle_song_items"] = shuffle_options["shuffle_song_items"].option_any
    #options["shopsanity"]
    #options["shop_slots"]
    #options["shopsanity_prices"]
    options["tokensanity"] = shuffle_options["tokensanity"].option_all
    options["shuffle_scrubs"] = shuffle_options["shuffle_scrubs"].option_random_prices
    options["shuffle_child_trade"] = shuffle_options["shuffle_child_trade"].option_shuffle
    #options["shuffle_freestanding_items"]
    #options["shuffle_pots"]
    #options["shuffle_crates"]
    #options["shuffle_cows"]
    #options["shuffle_beehives"]
    options["shuffle_kokiri_sword"] = shuffle_options["shuffle_kokiri_sword"].option_true
    options["shuffle_ocarinas"] = shuffle_options["shuffle_ocarinas"].option_true
    options["shuffle_gerudo_card"] = shuffle_options["shuffle_gerudo_card"].option_true
    options["shuffle_beans"] = shuffle_options["shuffle_beans"].option_true
    options["shuffle_medigoron_carpet_salesman"] = shuffle_options["shuffle_medigoron_carpet_salesman"].option_true
    #options["shuffle_frog_song_rupees"]
    return options
