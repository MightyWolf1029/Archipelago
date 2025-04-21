from .OoTR.Cosmetics import *
from .OoTR import Cosmetics as OoTRCosmetics

from . import Music as music

# Update OoTR's Cosmetics to use our Music
OoTRCosmetics.music = music

class MockSettings:
    """
    A class to mock OoTR's ``Settings`` class
    """
    def set_dict(self, ootworld):
        for key, value in ootworld.__dict__.items():
            if isinstance(value, str):
                if "sfx" in key:
                    self.__dict__[key] = format_cosmetic_option_result(value, "-", False)
                elif "color" in key:
                    self.__dict__[key] = format_cosmetic_option_result(value, " ", True)

    def __init__(self, ootworld):
        self.set_dict(ootworld)
        self.background_music = ootworld.background_music
        self.correct_model_colors = ootworld.correct_model_colors
        self.default_targeting = ootworld.default_targeting
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
    A class to mock OoTR's ``CosmeticsLog`` class
    """
    def __init__(self, settings):
        self.display_dpad = settings.display_dpad
        self.dpad_dungeon_menu = settings.dpad_dungeon_menu
        self.settings = settings
        self.src_dict = {}

# Patch OoTR's Settings and CosmeticsLog with our mocked versions
OoTRCosmetics.Settings = MockSettings
OoTRCosmetics.CosmeticsLog = MockLog

# Options are all lowercase and have underscores instead of spaces
# this needs to be undone for the oot generator
def format_cosmetic_option_result(option_result, delim, doCapitalize):
    def format_word(word, doCapitalize):
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

def patch_music(rom, settings, log, symbols):
    """
    Modified implementation of OoTR's ``patch_music`` function. Removes music
    mapping and the option to disable battle music
    """
    # patch music
    if settings.background_music != 'normal' or settings.fanfares != 'normal':
        music.restore_music(rom)
        log, errors = music.randomize_music(rom, settings, {})
        if errors:
            logger.error(errors)
    else:
        music.restore_music(rom)

def patch_model_colors(rom, color, model_addresses):
    """
    Modified implementation of OoTR's ``patch_model_colors`` function. Removes
    light addresses
    """
    main_addresses, dark_addresses = model_addresses

    if color is None:
        for address in main_addresses + dark_addresses:
            original = rom.original.read_bytes(address, 3)
            rom.write_bytes(address, original)
        return

    for address in main_addresses:
        rom.write_bytes(address, color)

    darkened_color = list(map(lambda light: int(max((light - 0x32) * 0.6, 0)), color))
    for address in dark_addresses:
        rom.write_bytes(address, darkened_color)

def patch_tunic_colors(rom, settings, log, symbols):
    """
    Modified implementation of OoTR's ``patch_tunic_colors`` function. Removes plando,
    removes logging, formats cosmetic options, uses ootworld's random
    """
    # patch tunic colors
    tunics = [
        ('Kokiri Tunic', 'kokiri_color', 0x00B6DA38),
        ('Goron Tunic',  'goron_color',  0x00B6DA3B),
        ('Zora Tunic',   'zora_color',   0x00B6DA3E),
    ]
    tunic_color_list = get_tunic_colors()

    for tunic, tunic_setting, address in tunics:
        tunic_option = settings.__dict__[tunic_setting]

        # handle random
        if tunic_option == 'Random Choice':
            tunic_option = settings.random.choice(tunic_color_list)
        # handle completely random
        if tunic_option == 'Completely Random':
            color = generate_random_color()
        # grab the color from the list
        elif tunic_option in tunic_colors:
            color = list(tunic_colors[tunic_option])
        # build color from hex code
        else:
            color = hex_to_color(tunic_option)
            tunic_option = 'Custom'
        # "Weird" weirdshots will crash if the Kokiri Tunic Green value is > 0x99 and possibly 0x98. Brickwall it.
        if settings.logic_rules != 'glitchless' and tunic == 'Kokiri Tunic':
            color[1] = min(color[1], 0x97)
        rom.write_bytes(address, color)

        # patch the tunic icon
        if [tunic, tunic_option] not in [['Kokiri Tunic', 'Kokiri Green'], ['Goron Tunic', 'Goron Red'], ['Zora Tunic', 'Zora Blue']]:
            patch_tunic_icon(rom, tunic, color)
        else:
            patch_tunic_icon(rom, tunic, None)

def patch_navi_colors(rom, settings, log, symbols):
    """
    Modified implementation of OoTR's ``patch_navi_colors`` function. Removes plando,
    removes logging, formats cosmetic options, uses ootworld's random
    """
    # patch navi colors
    navi = [
        # colors for Navi
        ('Navi Idle',            'navi_color_default',
         [0x00B5E184],  # Default (Player)
         symbols.get('CFG_RAINBOW_NAVI_IDLE_INNER_ENABLED', None), symbols.get('CFG_RAINBOW_NAVI_IDLE_OUTER_ENABLED', None)),
        ('Navi Targeting Enemy', 'navi_color_enemy',
            [0x00B5E19C, 0x00B5E1BC],  # Enemy, Boss
            symbols.get('CFG_RAINBOW_NAVI_ENEMY_INNER_ENABLED', None), symbols.get('CFG_RAINBOW_NAVI_ENEMY_OUTER_ENABLED', None)),
        ('Navi Targeting NPC',   'navi_color_npc',
            [0x00B5E194], # NPC
            symbols.get('CFG_RAINBOW_NAVI_NPC_INNER_ENABLED', None), symbols.get('CFG_RAINBOW_NAVI_NPC_OUTER_ENABLED', None)),
        ('Navi Targeting Prop',  'navi_color_prop',
            [0x00B5E174, 0x00B5E17C, 0x00B5E18C, 0x00B5E1A4, 0x00B5E1AC,
             0x00B5E1B4, 0x00B5E1C4, 0x00B5E1CC, 0x00B5E1D4], # Everything else
            symbols.get('CFG_RAINBOW_NAVI_PROP_INNER_ENABLED', None), symbols.get('CFG_RAINBOW_NAVI_PROP_OUTER_ENABLED', None)),
    ]

    navi_color_list = get_navi_colors()
    rainbow_error = None

    for navi_action, navi_setting, navi_addresses, rainbow_inner_symbol, rainbow_outer_symbol in navi:
        navi_option_inner = settings.__dict__[navi_setting+'_inner']
        navi_option_outer = settings.__dict__[navi_setting+'_outer']

        # choose a random choice for the whole group
        if navi_option_inner == 'Random Choice':
            navi_option_inner = settings.random.choice(navi_color_list)
        if navi_option_outer == 'Random Choice':
            navi_option_outer = settings.random.choice(navi_color_list)

        if navi_option_outer == 'Match Inner':
            navi_option_outer = navi_option_inner

        colors = []
        option_dict = {}
        for address_index, address in enumerate(navi_addresses):
            address_colors = {}
            colors.append(address_colors)
            for index, (navi_part, option, rainbow_symbol) in enumerate([
                ('inner', navi_option_inner, rainbow_inner_symbol),
                ('outer', navi_option_outer, rainbow_outer_symbol),
            ]):
                color = None

                # set rainbow option
                if rainbow_symbol is not None and option == 'Rainbow':
                    rom.write_byte(rainbow_symbol, 0x01)
                    color = [0x00, 0x00, 0x00]
                elif rainbow_symbol is not None:
                    rom.write_byte(rainbow_symbol, 0x00)
                elif option == 'Rainbow':
                    rainbow_error = "Rainbow Navi is not supported by this patch version. Using 'Completely Random' as a substitute."
                    option = 'Completely Random'

                # completely random is random for every subgroup
                if color is None and option == 'Completely Random':
                    color = generate_random_color()

                # grab the color from the list
                if color is None and option in NaviColors:
                    color = list(NaviColors[option][index])

                # build color from hex code
                if color is None:
                    color = hex_to_color(option)
                    option = 'Custom'

                # Check color validity
                if color is None:
                    raise Exception(f'Invalid {navi_part} color {option} for {navi_action}')

                address_colors[navi_part] = color
                option_dict[navi_part] = option

            # write color
            color = address_colors['inner'] + [0xFF] + address_colors['outer'] + [0xFF]
            rom.write_bytes(address, color)


    if rainbow_error:
        logger.error(rainbow_error)

def patch_sword_trails(rom, settings, log, symbols):
    """
    Modified implementation of OoTR's ``patch_sword_trails`` function. Removes plando,
    removes logging, formats cosmetic options, uses ootworld's random
    """
    # patch sword trail duration
    rom.write_byte(0x00BEFF8C, settings.sword_trail_duration)

    # patch sword trail colors
    sword_trails = [
        ('Sword Trail', 'sword_trail_color',
            [(0x00BEFF7C, 0xB0, 0x40, 0xB0, 0xFF), (0x00BEFF84, 0x20, 0x00, 0x10, 0x00)],
            symbols.get('CFG_RAINBOW_SWORD_INNER_ENABLED', None), symbols.get('CFG_RAINBOW_SWORD_OUTER_ENABLED', None)),
    ]

    sword_trail_color_list = get_sword_trail_colors()
    rainbow_error = None

    for trail_name, trail_setting, trail_addresses, rainbow_inner_symbol, rainbow_outer_symbol in sword_trails:
        option_inner = settings.__dict__[trail_setting+'_inner']
        option_outer = settings.__dict__[trail_setting+'_outer']

        # handle random choice
        if option_inner == 'Random Choice':
            option_inner = settings.random.choice(sword_trail_color_list)
        if option_outer == 'Random Choice':
            option_outer = settings.random.choice(sword_trail_color_list)

        if option_outer == 'Match Inner':
            option_outer = option_inner

        colors = []
        option_dict = {}
        for address_index, (address, inner_transparency, inner_white_transparency, outer_transparency, outer_white_transparency) in enumerate(trail_addresses):
            address_colors = {}
            colors.append(address_colors)
            transparency_dict = {}
            for index, (trail_part, option, rainbow_symbol, white_transparency, transparency) in enumerate([
                ('inner', option_inner, rainbow_inner_symbol, inner_white_transparency, inner_transparency),
                ('outer', option_outer, rainbow_outer_symbol, outer_white_transparency, outer_transparency),
            ]):
                color = None

                # set rainbow option
                if rainbow_symbol is not None and option == 'Rainbow':
                    rom.write_byte(rainbow_symbol, 0x01)
                    color = [0x00, 0x00, 0x00]
                elif rainbow_symbol is not None:
                    rom.write_byte(rainbow_symbol, 0x00)
                elif option == 'Rainbow':
                    rainbow_error = "Rainbow Sword Trail is not supported by this patch version. Using 'Completely Random' as a substitute."
                    option = 'Completely Random'

                # completely random is random for every subgroup
                if color is None and option == 'Completely Random':
                    color = generate_random_color()

                # grab the color from the list
                if color is None and option in sword_trail_colors:
                    color = list(sword_trail_colors[option])

                # build color from hex code
                if color is None:
                    color = hex_to_color(option)
                    option = 'Custom'

                # Check color validity
                if color is None:
                    raise Exception(f'Invalid {trail_part} color {option} for {trail_name}')

                # handle white transparency
                if option == 'White':
                    transparency_dict[trail_part] = white_transparency
                else:
                    transparency_dict[trail_part] = transparency

                address_colors[trail_part] = color
                option_dict[trail_part] = option

            # write color
            color = address_colors['outer'] + [transparency_dict['outer']] + address_colors['inner'] + [transparency_dict['inner']]
            rom.write_bytes(address, color)

    if rainbow_error:
        logger.error(rainbow_error)

def patch_trails(rom, settings, log, trails):
    """
    Modified implementation of OoTR's ``patch_trails`` function. Removes plando,
    removes logging, formats cosmetic options, uses ootworld's random
    """
    for trail_name, trail_setting, trail_color_list, trail_color_dict, trail_symbols in trails:
        color_inner_symbol, color_outer_symbol, rainbow_inner_symbol, rainbow_outer_symbol = trail_symbols
        option_inner = settings.__dict__[trail_setting+'_inner']
        option_outer = settings.__dict__[trail_setting+'_outer']

        # handle random choice
        if option_inner == 'Random Choice':
            option_inner = settings.random.choice(trail_color_list)
        if option_outer == 'Random Choice':
            option_outer = settings.random.choice(trail_color_list)

        if option_outer == 'Match Inner':
            option_outer = option_inner

        option_dict = {}
        colors = {}

        for index, (trail_part, option, rainbow_symbol, color_symbol) in enumerate([
            ('inner', option_inner, rainbow_inner_symbol, color_inner_symbol),
            ('outer', option_outer, rainbow_outer_symbol, color_outer_symbol),
        ]):
            color = None

            # set rainbow option
            if option == 'Rainbow':
                rom.write_byte(rainbow_symbol, 0x01)
                color = [0x00, 0x00, 0x00]
            else:
                rom.write_byte(rainbow_symbol, 0x00)

            # handle completely random
            if color is None and option == 'Completely Random':
                # Specific handling for inner bombchu trails for contrast purposes.
                if trail_name == 'Bombchu Trail' and trail_part == 'inner':
                    fixed_dark_color = [0, 0, 0]
                    color = [0, 0, 0]
                    # Avoid colors which have a low contrast so the bombchu ticking is still visible
                    while contrast_ratio(color, fixed_dark_color) <= 4:
                        color = generate_random_color()
                else:
                    color = generate_random_color()

            # grab the color from the list
            if color is None and option in trail_color_dict:
                color = list(trail_color_dict[option])

            # build color from hex code
            if color is None:
                color = hex_to_color(option)
                option = 'Custom'

            option_dict[trail_part] = option
            colors[trail_part] = color

            # write color
            rom.write_bytes(color_symbol, color)

def patch_gauntlet_colors(rom, settings, log, symbols):
    """
    Modified implementation of OoTR's ``patch_gauntlet_colors`` function. Removes plando,
    removes logging, formats cosmetic options, uses ootworld's random
    """
    # patch gauntlet colors
    gauntlets = [
        ('Silver Gauntlets', 'silver_gauntlets_color', 0x00B6DA44,
            ([0x173B4CC], [0x173B4D4, 0x173B50C, 0x173B514])), # GI Model DList colors
        ('Gold Gauntlets', 'golden_gauntlets_color',  0x00B6DA47,
            ([0x173B4EC], [0x173B4F4, 0x173B52C, 0x173B534])), # GI Model DList colors
    ]
    gauntlet_color_list = get_gauntlet_colors()

    for gauntlet, gauntlet_setting, address, model_addresses in gauntlets:
        gauntlet_option = settings.__dict__[gauntlet_setting]

        # handle random
        if gauntlet_option == 'Random Choice':
            gauntlet_option = settings.random.choice(gauntlet_color_list)
        # handle completely random
        if gauntlet_option == 'Completely Random':
            color = generate_random_color()
        # grab the color from the list
        elif gauntlet_option in gauntlet_colors:
            color = list(gauntlet_colors[gauntlet_option])
        # build color from hex code
        else:
            color = hex_to_color(gauntlet_option)
            gauntlet_option = 'Custom'
        rom.write_bytes(address, color)
        if settings.correct_model_colors:
            patch_model_colors(rom, color, model_addresses)
        else:
            patch_model_colors(rom, None, model_addresses)

def patch_shield_frame_colors(rom, settings, log, symbols):
    """
    Modified implementation of OoTR's ``patch_shield_frame_colors`` function. Removes plando,
    removes logging, formats cosmetic options, uses ootworld's random
    """
    # patch shield frame colors
    shield_frames = [
        ('Mirror Shield Frame', 'mirror_shield_frame_color',
            [0xFA7274, 0xFA776C, 0xFAA27C, 0xFAC564, 0xFAC984, 0xFAEDD4],
            ([0x1616FCC], [0x1616FD4])),
    ]
    shield_frame_color_list = get_shield_frame_colors()

    for shield_frame, shield_frame_setting, addresses, model_addresses in shield_frames:
        shield_frame_option = settings.__dict__[shield_frame_setting]

        # handle random
        if shield_frame_option == 'Random Choice':
            shield_frame_option = settings.random.choice(shield_frame_color_list)
        # handle completely random
        if shield_frame_option == 'Completely Random':
            color = [settings.random.getrandbits(8), settings.random.getrandbits(8), settings.random.getrandbits(8)]
        # grab the color from the list
        elif shield_frame_option in shield_frame_colors:
            color = list(shield_frame_colors[shield_frame_option])
        # build color from hex code
        else:
            color = hex_to_color(shield_frame_option)
            shield_frame_option = 'Custom'
        for address in addresses:
            rom.write_bytes(address, color)
        if settings.correct_model_colors and shield_frame_option != 'Red':
            patch_model_colors(rom, color, model_addresses)
        else:
            patch_model_colors(rom, None, model_addresses)

def patch_heart_colors(rom, settings, log, symbols):
    """
    Modified implementation of OoTR's ``patch_heart_colors`` function. Removes plando,
    removes logging, removes potion colors, formats cosmetic options, uses ootworld's random
    """
    # patch heart colors
    hearts = [
        ('Heart Color', 'heart_color', symbols['CFG_HEART_COLOR'], 0xBB0994,
            ([0x14DA474, 0x14DA594, 0x14B701C, 0x14B70DC],
             [0x14B70FC, 0x14DA494, 0x14DA5B4, 0x14B700C, 0x14B702C, 0x14B703C, 0x14B704C, 0x14B705C,
              0x14B706C, 0x14B707C, 0x14B708C, 0x14B709C, 0x14B70AC, 0x14B70BC, 0x14B70CC])), # GI Model DList colors
    ]
    heart_color_list = get_heart_colors()

    for heart, heart_setting, symbol, file_select_address, model_addresses in hearts:
        heart_option = settings.__dict__[heart_setting]

        # handle random
        if heart_option == 'Random Choice':
            heart_option = settings.random.choice(heart_color_list)
        # handle completely random
        if heart_option == 'Completely Random':
            color = generate_random_color()
        # grab the color from the list
        elif heart_option in heart_colors:
            color = list(heart_colors[heart_option])
        # build color from hex code
        else:
            color = hex_to_color(heart_option)
            heart_option = 'Custom'
        rom.write_int16s(symbol, color) # symbol for ingame HUD
        rom.write_int16s(file_select_address, color) # file select normal hearts
        if heart_option != 'Red':
            rom.write_int16s(file_select_address + 6, color) # file select DD hearts
        else:
            original_dd_color = rom.original.read_bytes(file_select_address + 6, 6)
            rom.write_bytes(file_select_address + 6, original_dd_color)
        if settings.correct_model_colors and heart_option != 'Red':
            patch_model_colors(rom, color, model_addresses) # heart model colors
            icon.patch_overworld_icon(rom, color, 0xF43D80) # Overworld Heart Icon
        else:
            patch_model_colors(rom, None, model_addresses)
            icon.patch_overworld_icon(rom, None, 0xF43D80)

def patch_magic_colors(rom, settings, log, symbols):
    """
    Modified implementation of OoTR's ``patch_magic_colors`` function. Removes plando,
    removes logging, removes potion colors, formats cosmetic options, uses ootworld's random
    """
    # patch magic colors
    magic = [
        ('Magic Meter Color', 'magic_color', symbols["CFG_MAGIC_COLOR"],
            ([0x154C654, 0x154CFB4], [0x154C65C, 0x154CFBC])), # GI Model DList colors
    ]
    magic_color_list = get_magic_colors()

    for magic_color, magic_setting, symbol, model_addresses in magic:
        magic_option = settings.__dict__[magic_setting]

        if magic_option == 'Random Choice':
           magic_option = settings.random.choice(magic_color_list)

        if magic_option == 'Completely Random':
            color = generate_random_color()
        elif magic_option in magic_colors:
            color = list(magic_colors[magic_option])
        else:
            color = hex_to_color(magic_option)
            magic_option = 'Custom'
        rom.write_int16s(symbol, color)
        if magic_option != 'Green' and settings.correct_model_colors:
            patch_model_colors(rom, color, model_addresses)
            icon.patch_overworld_icon(rom, color, 0xF45650, data_path('icons/magicSmallExtras.raw')) # Overworld Small Pot
            icon.patch_overworld_icon(rom, color, 0xF47650, data_path('icons/magicLargeExtras.raw')) # Overworld Big Pot
        else:
            patch_model_colors(rom, None, model_addresses)
            icon.patch_overworld_icon(rom, None, 0xF45650)
            icon.patch_overworld_icon(rom, None, 0xF47650)

def patch_button_colors(rom, settings, log, symbols):
    """
    Modified implementation of OoTR's ``patch_button_colors`` function. Removes plando,
    removes logging, formats cosmetic options, uses ootworld's random
    """
    buttons = [
        ('A Button Color', 'a_button_color', a_button_colors,
            [('A Button Color', symbols['CFG_A_BUTTON_COLOR'],
                None),
             ('Text Cursor Color', symbols['CFG_TEXT_CURSOR_COLOR'],
                [(0xB88E81, 0xB88E85, 0xB88E9)]), # Initial Inner Color
             ('Shop Cursor Color', symbols['CFG_SHOP_CURSOR_COLOR'],
                None),
             ('Save/Death Cursor Color', None,
                [(0xBBEBC2, 0xBBEBC3, 0xBBEBD6), (0xBBEDDA, 0xBBEDDB, 0xBBEDDE)]), # Save Cursor / Death Cursor
             ('Pause Menu A Cursor Color', None,
                [(0xBC7849, 0xBC784B, 0xBC784D), (0xBC78A9, 0xBC78AB, 0xBC78AD), (0xBC78BB, 0xBC78BD, 0xBC78BF)]), # Inner / Pulse 1 / Pulse 2
             ('Pause Menu A Icon Color', None,
                [(0x845754, 0x845755, 0x845756)]),
             ('A Note Color', symbols['CFG_A_NOTE_COLOR'], # For Textbox Song Display
                [(0xBB299A, 0xBB299B, 0xBB299E), (0xBB2C8E, 0xBB2C8F, 0xBB2C92), (0xBB2F8A, 0xBB2F8B, 0xBB2F96)]), # Pause Menu Song Display
            ]),
        ('B Button Color', 'b_button_color', b_button_colors,
            [('B Button Color', symbols['CFG_B_BUTTON_COLOR'],
                None),
            ]),
        ('C Button Color', 'c_button_color', c_button_colors,
            [('C Button Color', symbols['CFG_C_BUTTON_COLOR'],
                None),
             ('Pause Menu C Cursor Color', None,
                [(0xBC7843, 0xBC7845, 0xBC7847), (0xBC7891, 0xBC7893, 0xBC7895), (0xBC78A3, 0xBC78A5, 0xBC78A7)]), # Inner / Pulse 1 / Pulse 2
             ('Pause Menu C Icon Color', None,
                [(0x8456FC, 0x8456FD, 0x8456FE)]),
             ('C Note Color', symbols['CFG_C_NOTE_COLOR'], # For Textbox Song Display
                [(0xBB2996, 0xBB2997, 0xBB29A2), (0xBB2C8A, 0xBB2C8B, 0xBB2C96), (0xBB2F86, 0xBB2F87, 0xBB2F9A)]), # Pause Menu Song Display
            ]),
        ('Start Button Color', 'start_button_color', start_button_colors,
            [('Start Button Color', None,
                [(0xAE9EC6, 0xAE9EC7, 0xAE9EDA)]),
            ]),
    ]

    for button, button_setting, button_colors, patches in buttons:
        button_option = settings.__dict__[button_setting]
        color_set = None
        colors = {}

        # handle random
        if button_option == 'Random Choice':
            button_option = settings.random.choice(list(button_colors.keys()))
        # handle completely random
        if button_option == 'Completely Random':
            fixed_font_color = [10, 10, 10]
            color = [0, 0, 0]
            # Avoid colors which have a low contrast with the font inside buttons (eg. the A letter)
            while contrast_ratio(color, fixed_font_color) <= 3:
                color = generate_random_color()
        # grab the color from the list
        elif button_option in button_colors:
            color_set = [button_colors[button_option]] if isinstance(button_colors[button_option][0], int) else list(button_colors[button_option])
            color = color_set[0]
        # build color from hex code
        else:
            color = hex_to_color(button_option)
            button_option = 'Custom'

        # apply all button color patches
        for i, (patch, symbol, byte_addresses) in enumerate(patches):
            if color_set is not None and len(color_set) > i and color_set[i]:
                colors[patch] = color_set[i]
            else:
                colors[patch] = color

            if symbol:
                rom.write_int16s(symbol, colors[patch])

            if byte_addresses:
                for r_addr, g_addr, b_addr in byte_addresses:
                    rom.write_byte(r_addr, colors[patch][0])
                    rom.write_byte(g_addr, colors[patch][1])
                    rom.write_byte(b_addr, colors[patch][2])

def patch_sfx(rom, settings, log, symbols):
    """
    Modified implementation of OoTR's ``patch_sfx`` function. Removes plando,
    removes logging, formats cosmetic options, uses ootworld's random
    """
    # Configurable Sound Effects
    sfx_config = [
          ('sfx_navi_overworld', sfx.SoundHooks.NAVI_OVERWORLD),
          ('sfx_navi_enemy',     sfx.SoundHooks.NAVI_ENEMY),
          ('sfx_low_hp',         sfx.SoundHooks.HP_LOW),
          ('sfx_menu_cursor',    sfx.SoundHooks.MENU_CURSOR),
          ('sfx_menu_select',    sfx.SoundHooks.MENU_SELECT),
          ('sfx_nightfall',      sfx.SoundHooks.NIGHTFALL),
          ('sfx_horse_neigh',    sfx.SoundHooks.HORSE_NEIGH),
          ('sfx_hover_boots',    sfx.SoundHooks.BOOTS_HOVER),
    ]
    sound_dict = sfx.get_patch_dict()
    sounds_keyword_label = {sound.value.keyword: sound.value.label for sound in sfx.Sounds}
    sounds_label_keyword = {sound.value.label: sound.value.keyword for sound in sfx.Sounds}

    for setting, hook in sfx_config:
        selection = settings.__dict__[setting].replace('_', '-')

        if selection == 'default':
            for loc in hook.value.locations:
                sound_id = rom.original.read_int16(loc)
                rom.write_int16(loc, sound_id)
        else:
            if selection == 'random-choice':
                selection = settings.random.choice(sfx.get_hook_pool(hook)).value.keyword
            elif selection == 'random-ear-safe':
                selection = settings.random.choice(sfx.get_hook_pool(hook, "TRUE")).value.keyword
            elif selection == 'completely-random':
                selection = settings.random.choice(sfx.standard).value.keyword
            sound_id  = sound_dict[selection]
            for loc in hook.value.locations:
                rom.write_int16(loc, sound_id)

def patch_instrument(rom, settings, log, symbols):
    """
    Modified implementation of OoTR's ``patch_instrument`` function. Removes logging,
    uses ootworld's random
    """
    # Player Instrument
    instruments = {
           #'none':            0x00,
            'ocarina':         0x01,
            'malon':           0x02,
            'whistle':         0x03,
            'harp':            0x04,
            'grind_organ':     0x05,
            'flute':           0x06,
           #'another_ocarina': 0x07,
    }

    choice = settings.sfx_ocarina
    if choice == 'random-choice':
        choice = settings.random.choice(list(instruments.keys()))

    rom.write_byte(0x00B53C7B, instruments[choice])
    rom.write_byte(0x00B4BF6F, instruments[choice]) # For Lost Woods Skull Kids' minigame in Lost Woods

ap_patch_sets = {}
# 3.14.1
ap_patch_sets[0x1F04FA62] = {
    "patches": [
        patch_dpad,
        patch_sword_trails
    ],
    "symbols" : patch_sets[0x1F04FA62]["symbols"]
}
# 3.14.11
ap_patch_sets[0x1F05D3F9] = {
    "patches": ap_patch_sets[0x1F04FA62]["patches"] + [],
    "symbols" : patch_sets[0x1F05D3F9]["symbols"]
}
# 4.5.7
ap_patch_sets[0x1F0693FB] = {
    "patches": ap_patch_sets[0x1F05D3F9]["patches"] + [
        patch_heart_colors,
        patch_magic_colors,
    ],
    "symbols": patch_sets[0x1F0693FB]["symbols"]
}
# 5.2.6
ap_patch_sets[0x1F073FC9] = {
    "patches": ap_patch_sets[0x1F0693FB]["patches"] + [
        patch_button_colors,
    ],
    "symbols": patch_sets[0x1F073FC9]["symbols"]
}
# 5.2.76
ap_patch_sets[0x1F073FD8] = {
    "patches": ap_patch_sets[0x1F073FC9]["patches"] + [
        patch_navi_colors,
        patch_boomerang_trails,
        patch_bombchu_trails,
    ],
    "symbols": patch_sets[0x1F073FD8]["symbols"]
}
# 6.2.218
ap_patch_sets[0x1F073FD9] = {
    "patches": ap_patch_sets[0x1F073FD8]["patches"] + [
        patch_dpad_info,
    ],
    "symbols": patch_sets[0x1F073FD9]["symbols"]
}

# Update OoTR's Cosmetics to use the patched version
OoTRCosmetics.patch_trails = patch_trails

def update_patch_sets():
    # Remove functions from global_patch_sets that we will be modifying
    global_patch_sets.remove(OoTRCosmetics.patch_music)
    global_patch_sets.remove(OoTRCosmetics.patch_tunic_colors)
    global_patch_sets.remove(OoTRCosmetics.patch_navi_colors)
    global_patch_sets.remove(OoTRCosmetics.patch_sword_trails)
    global_patch_sets.remove(OoTRCosmetics.patch_gauntlet_colors)
    global_patch_sets.remove(OoTRCosmetics.patch_shield_frame_colors)
    global_patch_sets.remove(OoTRCosmetics.patch_voices) # We do not use patch_voices
    global_patch_sets.remove(OoTRCosmetics.patch_sfx)
    global_patch_sets.remove(OoTRCosmetics.patch_instrument)

    # Update global_patch_sets to use the modified versions
    global_patch_sets.append(patch_music)
    global_patch_sets.append(patch_tunic_colors)
    global_patch_sets.append(patch_navi_colors)
    global_patch_sets.append(patch_sword_trails)
    global_patch_sets.append(patch_gauntlet_colors)
    global_patch_sets.append(patch_shield_frame_colors)
    global_patch_sets.append(patch_sfx)
    global_patch_sets.append(patch_instrument)

def patch_cosmetics(ootworld, rom):
    """
    Modified implementation of OoTR's ``patch_cosmetics``. It creates mocked versions of OoTR's ``Settings``
    and ``CosmeticsLog`` classes to enable calling the original patch helper functions. The function
    no longer returns the ``CosmeticsLog``. It also logs errors to the python ``logger``.
    """
    ########################
    # Begin AP modified code
    OoTRCosmetics.random = ootworld.random
    update_patch_sets()
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
        versioned_patch_set = ap_patch_sets.get(cosmetic_version)
    else:
        # If cosmetic_context is not a valid pointer, then try to
        # search over all possible legacy header locations.
        for header in legacy_cosmetic_data_headers:
            cosmetic_context = header
            cosmetic_version = rom.read_int32(cosmetic_context)
            if cosmetic_version in ap_patch_sets:
                versioned_patch_set = ap_patch_sets[cosmetic_version]
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
