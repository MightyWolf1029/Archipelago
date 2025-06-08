from .OoTR.Cosmetics import *
from .OoTR import Cosmetics as OoTRCosmetics

from . import Music as music

logger = logging.getLogger('')

# Update OoTR's Cosmetics to use our Music
OoTRCosmetics.music = music

class MockSettings:
    """
    A class to mock OoTR's ``Settings`` class.
    """
    def set_dict(self, ootworld):
        for key, value in ootworld.__dict__.items():
            if isinstance(value, str):
                if "sfx" in key:
                    self.__dict__[key] = format_cosmetic_option_result(value, "-", False)
                elif "color" in key:
                    self.__dict__[key] = format_cosmetic_option_result(value, " ", True)
                if "match_inner" in value:
                    self.__dict__[key] = "[Same as Inner]"

    def __init__(self, ootworld):
        self.set_dict(ootworld)
        self.background_music = ootworld.background_music
        self.correct_model_colors = ootworld.correct_model_colors
        self.default_targeting = ootworld.default_targeting
        self.disable_battle_music = False # Not supported
        self.display_dpad = ootworld.display_dpad
        self.dpad_dungeon_menu = ootworld.dpad_dungeon_menu
        self.fanfares = ootworld.fanfares
        self.logic_rules = ootworld.logic_rules
        self.ocarina_fanfares = ootworld.ocarina_fanfares
        self.random = ootworld.random
        self.settings = ootworld.settings
        self.sfx_ocarina = ootworld.sfx_ocarina
        self.sword_trail_duration = ootworld.sword_trail_duration

class MockLog:
    """
    A class to mock OoTR's ``CosmeticsLog`` class.
    """
    def __init__(self, settings):
        self.bgm = {}
        self.display_dpad = settings.display_dpad
        self.dpad_dungeon_menu = settings.dpad_dungeon_menu
        self.equipment_colors = {}
        self.errors = []
        self.misc_colors = {}
        self.settings = settings
        self.sfx = {}
        self.src_dict = {}
        self.ui_colors = {}

class MockSettingInfo:
    """
    A class to mock OoTR's ``Setting_Info`` object from SettingsList.
    """
    def __init__(self):
        self.name = 'sfx_ocarina'
        # Taken from patch_instruments' dict of instruments
        self.choices = {
            'ocarina':         0x01,
            'malon':           0x02,
            'whistle':         0x03,
            'harp':            0x04,
            'grind_organ':     0x05,
            'flute':           0x06,
        }

# Patch OoTR's Settings and CosmeticsLog with our mocked versions
OoTRCosmetics.Settings = MockSettings
OoTRCosmetics.CosmeticsLog = MockLog

# Update setting_infos (used by OoTR's patch_instrument)
OoTRCosmetics.setting_infos = []
OoTRCosmetics.setting_infos.append(MockSettingInfo())

# Options are all lowercase and have underscores instead of spaces
# this needs to be undone for the oot generator
def format_cosmetic_option_result(option_result, delim, doCapitalize):
    """
    Helper function to format ootworld's settings strings so that OoTR can parse them.
    Args:
        option_result: the setting string to be formatted
        delim: the delimiter to use between words
        doCapitalize: flag to indicate if words should be capitalized
    Returns:
        The formatted settings string
    """
    def format_word(word, doCapitalize):
        """
        Inner function to handle formatting individual words.
        Args:
            word: the word for be formatted
            doCapitalize: flag to indicate if the word should be capitalized
        Returns:
            The formatted word
        """
        # Words that use special capitalization
        special_words = {
            'nes': 'NES',
            'gamecube': 'GameCube',
            'of': 'of'
        }
        if doCapitalize:
            return special_words.get(word, word.capitalize())
        else:
            return special_words.get(word, word)
    words = option_result.split('_')
    return delim.join([format_word(word, doCapitalize) for word in words])

def patch_cosmetics(ootworld, rom):
    """
    Modified implementation of OoTR's ``patch_cosmetics``. It creates mocked versions of OoTR's ``Settings``
    and ``CosmeticsLog`` classes to enable calling the original patch helper functions. The function
    no longer returns the ``CosmeticsLog``. It also logs errors to the python ``logger``.
    """
    ########################
    # Begin AP modified code
    OoTRCosmetics.random = ootworld.random
    if global_patch_sets.__contains__(OoTRCosmetics.patch_voices):
        global_patch_sets.remove(OoTRCosmetics.patch_voices) # We do not use patch_voices
    # Convert the ootworld to a mocked OoTR Settings object so we can call the base methods wherever possible
    settings = MockSettings(ootworld)
    # Use this Settings object to construct a CosmeticsLog object
    log = MockLog(settings)
    # End AP modified code
    ########################

    # try to detect the cosmetic patch data format
    cosmetic_version = None
    versioned_patch_set = None
    cosmetic_context = rom.read_int32(rom.sym('RANDO_CONTEXT') + 4)
    if cosmetic_context >= 0x80000000 and cosmetic_context <= 0x80F7FFFC:
        cosmetic_context = (cosmetic_context - 0x80400000) + 0x3480000 # convert from RAM to ROM address
        cosmetic_version = rom.read_int32(cosmetic_context)
        versioned_patch_set = OoTRCosmetics.patch_sets.get(cosmetic_version)
    else:
        # If cosmetic_context is not a valid pointer, then try to
        # search over all possible legacy header locations.
        for header in legacy_cosmetic_data_headers:
            cosmetic_context = header
            cosmetic_version = rom.read_int32(cosmetic_context)
            if cosmetic_version in OoTRCosmetics.patch_sets:
                versioned_patch_set = OoTRCosmetics.patch_sets[cosmetic_version]
                break

    # patch version specific patches
    if versioned_patch_set:
        # offset the cosmetic_context struct for absolute addressing
        cosmetic_context_symbols = {
            sym: address + cosmetic_context
            for sym, address in versioned_patch_set['symbols'].items()
        }

        # warn if patching a legacy format
        if cosmetic_version != rom.read_int32(rom.sym('COSMETIC_FORMAT_VERSION')):
            ########################
            # Begin AP modified code
            logger.error("ROM uses old cosmetic patch format.")
            # End AP modified code
            ########################

        # patch cosmetics that use vanilla oot data, and always compatible
        for patch_func in [patch for patch in global_patch_sets if patch not in versioned_patch_set['patches']]:
            patch_func(rom, settings, log, {})

        for patch_func in versioned_patch_set['patches']:
            patch_func(rom, settings, log, cosmetic_context_symbols)
    else:
        # patch cosmetics that use vanilla oot data, and always compatible
        for patch_func in global_patch_sets:
            patch_func(rom, settings, log, {})

        ########################
        # Begin AP modified code
        # Unknown patch format
        logger.error("Unable to patch some cosmetics. ROM uses unknown cosmetic patch format.")
        # End AP modified code
        ########################

    ########################
    # Begin AP modified code
    # Log all the errors encountered during patching
    for error in log.errors:
        logger.error(error)
    # End AP modified code
    ########################