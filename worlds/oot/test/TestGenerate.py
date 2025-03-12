import typing

from . import OOTTestBase, all_options, max_shuffle
from ..Options import open_options, world_options, bridge_options, shuffle_options, dungeon_items_options, timesavers_options, \
    misc_options, itempool_options, cosmetic_options, sfx_options

class TestGenerateKeysanity(OOTTestBase):
    """Test that the key shuffle settings generate the correct keys in the correct locations"""

    def update_small_key_setting(self, key_opt: typing.Any):
        self.options["shuffle_smallkeys"] = key_opt
        self.setUp()

    def test_no_keys_added(self):
        self.update_small_key_setting(dungeon_items_options["shuffle_smallkeys"].option_remove)
        all_small_keys: typing.List[str] = [item.name for item in self.multiworld.itempool if "Small Key" in item.name]
        self.assertEqual(len(all_small_keys), 0, "Expected 0 Small Keys")

    def test_no_keys_added_vanilla(self):
        self.update_small_key_setting(dungeon_items_options["shuffle_smallkeys"].option_vanilla)
        all_small_keys: typing.List[str] = [item.name for item in self.multiworld.itempool if "Small Key" in item.name]
        self.assertEqual(len(all_small_keys), 0, "Expected 0 Small Keys")

    def test_dungeon_keys_added(self):
        self.update_small_key_setting(dungeon_items_options["shuffle_smallkeys"].option_dungeon)
        all_small_keys: typing.List[str] = [item.name for item in self.multiworld.itempool if "Small Key" in item.name]
        self.assertEqual(len(all_small_keys), 0, "Expected 0 Small Keys")

    def test_regional_keys_added(self):
        self.update_small_key_setting(dungeon_items_options["shuffle_smallkeys"].option_regional)
        all_small_keys: typing.List[str] = [item.name for item in self.multiworld.itempool if "Small Key" in item.name]
        self.assertEqual(len(all_small_keys), 0, "Expected 0 Small Keys")

    def test_overworld_keys_added(self):
        self.update_small_key_setting(dungeon_items_options["shuffle_smallkeys"].option_overworld)
        all_small_keys: typing.List[str] = [item.name for item in self.multiworld.itempool if "Small Key" in item.name]
        self.assertEqual(len(all_small_keys), 0, "Expected 0 Small Keys")

    def test_any_dungeon_keys_added(self):
        self.update_small_key_setting(dungeon_items_options["shuffle_smallkeys"].option_any_dungeon)
        all_small_keys: typing.List[str] = [item.name for item in self.multiworld.itempool if "Small Key" in item.name]
        self.assertEqual(len(all_small_keys), 0, "Expected 0 Small Keys")

    def test_anywhere_keys_added(self):
        self.update_small_key_setting(dungeon_items_options["shuffle_smallkeys"].option_keysanity)
        all_small_keys: typing.List[str] = [item.name for item in self.multiworld.itempool if "Small Key" in item.name]
        print(self.multiworld.itempool)
        self.assertEqual(len([key for key in all_small_keys if key == "Small Key (Forest Temple)"]), 5, "Expected 5 Forest Temple Small Keys")
        self.assertEqual(len([key for key in all_small_keys if key == "Small Key (Fire Temple)"]), 8, "Expected 8 Fire Temple Small Keys")
        self.assertEqual(len([key for key in all_small_keys if key == "Small Key (Water Temple)"]), 6, "Expected 6 Water Temple Small Keys")
        self.assertEqual(len([key for key in all_small_keys if key == "Small Key (Shadow Temple)"]), 5, "Expected 5 Shadow Temple Small Keys")
        self.assertEqual(len([key for key in all_small_keys if key == "Small Key (Spirit Temple)"]), 5, "Expected 5 Spirit Temple Small Keys")
        self.assertEqual(len([key for key in all_small_keys if key == "Small Key (Gerudo Training Ground)"]), 9, "Expected 9 Gerudo Training Ground Small Keys")
        self.assertEqual(len([key for key in all_small_keys if key == "Small Key (Bottom of the Well)"]), 3, "Expected 3 Bottom of the Well Small Keys")
        self.assertEqual(len([key for key in all_small_keys if key == "Small Key (Ganons Castle)"]), 2, "Expected 2 Ganon's Castle Small Keys")

class TestGenerateSkullsanity(OOTTestBase):
    """Test that the Gold Skulltula Token settings generate the correct number of tokens"""

    def update_skull_setting(self, skull_opt: typing.Any):
        self.options["tokensanity"] = skull_opt
        self.setUp()

    def test_no_skull_tokens_added(self):
        self.update_skull_setting(shuffle_options["tokensanity"].option_off)
        all_tokens: typing.List[str] = [item.name for item in self.multiworld.itempool if item.name == "Gold Skulltula Token"]
        self.assertEqual(len(all_tokens), 0, "Expected 0 Gold Skulltula Tokens")

    def test_dungeon_skull_tokens_added(self):
        self.update_skull_setting(shuffle_options["tokensanity"].option_dungeons)
        all_tokens: typing.List[str] = [item.name for item in self.multiworld.itempool if item.name == "Gold Skulltula Token"]
        self.assertEqual(len(all_tokens), 44, "Expected 44 Gold Skulltula Tokens")

    def test_overworld_skull_tokens_added(self):
        self.update_skull_setting(shuffle_options["tokensanity"].option_overworld)
        all_tokens: typing.List[str] = [item.name for item in self.multiworld.itempool if item.name == "Gold Skulltula Token"]
        self.assertEqual(len(all_tokens), 56, "Expected 56 Gold Skulltula Tokens")

    def test_all_skull_tokens_added(self):
        self.update_skull_setting(shuffle_options["tokensanity"].option_all)
        all_tokens: typing.List[str] = [item.name for item in self.multiworld.itempool if item.name == "Gold Skulltula Token"]
        self.assertEqual(len(all_tokens), 100, "Expected 100 Gold Skulltula Tokens")

class TestGenerateDefault(OOTTestBase):
    # If we don't set options, everything is set to the default
    options = {}
    for name, opt in all_options().items():
        options[name] = opt.default if hasattr(opt, "default") else 0
        print(name + " defaulting to " + str(options[name]))
    options = options | max_shuffle()
