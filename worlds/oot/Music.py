from .OoTR.Music import *
from .OoTR import Music as OoTRMusic

def shuffle_music(sequences, target_sequences, music_mapping, log, rand):
    """
    Modified to accept an additional parameter `rand`
    """

    sequence_dict = {}
    sequence_ids = []

    for sequence in sequences:
        if sequence.cosmetic_name == "None":
            raise Exception('Sequences should not be named "None" as that is used for disabled music. Sequence with improper name: %s' % sequence.name)
        if sequence.cosmetic_name in sequence_dict:
            raise Exception('Sequence names should be unique. Duplicate sequence name: %s' % sequence.cosmetic_name)
        sequence_dict[sequence.cosmetic_name] = sequence
        if sequence.cosmetic_name not in music_mapping.values():
            sequence_ids.append(sequence.cosmetic_name)

    # Shuffle the sequences
    if len(sequences) < len(target_sequences):
        raise Exception(f"Not enough custom music/fanfares ({len(sequences)}) to omit base Ocarina of Time sequences ({len(target_sequences)}).")
    ########################
    # Begin AP modified code
    rand.shuffle(sequence_ids)
    # End AP modified code
    ########################

    sequences = []
    for target_sequence in target_sequences:
        sequence = sequence_dict[sequence_ids.pop()].copy() if target_sequence.cosmetic_name not in music_mapping \
            else ("None", 0x0) if music_mapping[target_sequence.cosmetic_name] == "None" \
            else sequence_dict[music_mapping[target_sequence.cosmetic_name]].copy()
        sequences.append(sequence)
        sequence.replaces = target_sequence.replaces
        log[target_sequence.cosmetic_name] = sequence.cosmetic_name

    return sequences, log

# Update the original file to use the modified function
OoTRMusic.shuffle_music = shuffle_music

def shuffle_pointers_table(rom, ids, music_mapping, log, rand):
    """
    Modified to accept an additional parameter `rand`
    """
    # Read in all the Music data
    bgm_data = {}
    bgm_ids = []

    for bgm in ids:
        bgm_sequence = rom.read_bytes(0xB89AE0 + (bgm[1] * 0x10), 0x10)
        bgm_instrument = rom.read_int16(0xB89910 + 0xDD + (bgm[1] * 2))
        bgm_data[bgm[0]] = (bgm[0], bgm_sequence, bgm_instrument)
        if bgm[0] not in music_mapping.values():
            bgm_ids.append(bgm[0])

    ########################
    # Begin AP modified code
    # shuffle data
    rand.shuffle(bgm_ids)
    # End AP modified code
    ########################

    # Write Music data back in random ordering
    for bgm in ids:
        if bgm[0] in music_mapping and music_mapping[bgm[0]] in bgm_data:
            bgm_name = music_mapping[bgm[0]]
        else:
            bgm_name = bgm_ids.pop()
        bgm_name, bgm_sequence, bgm_instrument = bgm_data[bgm_name]
        rom.write_bytes(0xB89AE0 + (bgm[1] * 0x10), bgm_sequence)
        rom.write_int16(0xB89910 + 0xDD + (bgm[1] * 2), bgm_instrument)
        log[bgm[0]] = bgm_name

    # Write Fairy Fountain instrument to File Select (uses same track but different instrument set pointer for some reason)
    rom.write_int16(0xB89910 + 0xDD + (0x57 * 2), rom.read_int16(0xB89910 + 0xDD + (0x28 * 2)))
    return log

# Update the original file to use the modified function
OoTRMusic.shuffle_pointers_table = shuffle_pointers_table

def randomize_music(rom, ootworld, music_mapping):
    """
    Modified to accept ootworld instead of settings, remove custom audio
    """
    log = {}
    errors = []
    sequences = []
    target_sequences = []
    fanfare_sequences = []
    fanfare_target_sequences = []
    disabled_source_sequences = {}
    disabled_target_sequences = {}

    # Make sure we aren't operating directly on these.
    music_mapping = music_mapping.copy()
    bgm_ids = bgm_sequence_ids.copy()
    ff_ids = fanfare_sequence_ids.copy()

    # Check if we have mapped music for BGM, Fanfares, or Ocarina Fanfares
    bgm_mapped = any(bgm[0] in music_mapping for bgm in bgm_ids)
    ff_mapped = any(ff[0] in music_mapping for ff in ff_ids)
    ocarina_mapped = any(ocarina[0] in music_mapping for ocarina in ocarina_sequence_ids)

    # Include ocarina songs in fanfare pool if checked
    if ootworld.ocarina_fanfares or ocarina_mapped:
        ff_ids.extend(ocarina_sequence_ids)

    # Flag sequence locations that are set to off for disabling.
    disabled_ids = []
    if ootworld.background_music == 'off':
        disabled_ids += [music_id for music_id in bgm_ids]
    if ootworld.fanfares == 'off':
        disabled_ids += [music_id for music_id in ff_ids]
        disabled_ids += [music_id for music_id in ocarina_sequence_ids]
    for bgm in [music_id for music_id in bgm_ids + ff_ids + ocarina_sequence_ids]:
        if music_mapping.get(bgm[0], '') == "None":
            disabled_target_sequences[bgm[0]] = bgm
    for bgm in disabled_ids:
        if bgm[0] not in music_mapping:
            music_mapping[bgm[0]] = "None"
            disabled_target_sequences[bgm[0]] = bgm

    # Map music to itself if music is set to normal.
    normal_ids = []
    if ootworld.background_music == 'normal' and bgm_mapped:
        normal_ids += [music_id for music_id in bgm_ids]
    if ootworld.fanfares == 'normal' and (ff_mapped or ocarina_mapped):
        normal_ids += [music_id for music_id in ff_ids]
    if not ootworld.ocarina_fanfares and ootworld.fanfares == 'normal' and ocarina_mapped:
        normal_ids += [music_id for music_id in ocarina_sequence_ids]
    for bgm in normal_ids:
        if bgm[0] not in music_mapping:
            music_mapping[bgm[0]] = bgm[0]

    ########################
    # Begin AP modified code
    # If not creating patch file, shuffle audio sequences. Otherwise, shuffle pointer table
    # If generating from patch, also do a version check to make sure custom sequences are supported.
    # custom_sequences_enabled = ootworld.compress_rom != 'Patch'
    # if ootworld.patch_file != '':
    #     rom_version_bytes = rom.read_bytes(0x35, 3)
    #     rom_version = f'{rom_version_bytes[0]}.{rom_version_bytes[1]}.{rom_version_bytes[2]}'
    #     if compare_version(rom_version, '4.11.13') < 0:
    #         errors.append("Custom music is not supported by this patch version. Only randomizing vanilla music.")
    #         custom_sequences_enabled = False
    # if custom_sequences_enabled:
    #     if ootworld.background_music in ['random', 'random_custom_only'] or bgm_mapped:
    #         process_sequences(rom, sequences, target_sequences, disabled_source_sequences, disabled_target_sequences, bgm_ids)
    #         if ootworld.background_music == 'random_custom_only':
    #             sequences = [seq for seq in sequences if seq.cosmetic_name not in [x[0] for x in bgm_ids] or seq.cosmetic_name in music_mapping.values()]
    #         sequences, log = shuffle_music(sequences, target_sequences, music_mapping, log, ootworld.random)

    #     if ootworld.fanfares in ['random', 'random_custom_only'] or ff_mapped or ocarina_mapped:
    #         process_sequences(rom, fanfare_sequences, fanfare_target_sequences, disabled_source_sequences, disabled_target_sequences, ff_ids, 'fanfare')
    #         if ootworld.fanfares == 'random_custom_only':
    #             fanfare_sequences = [seq for seq in fanfare_sequences if seq.cosmetic_name not in [x[0] for x in fanfare_sequence_ids] or seq.cosmetic_name in music_mapping.values()]
    #         fanfare_sequences, log = shuffle_music(fanfare_sequences, fanfare_target_sequences, music_mapping, log, ootworld.random)

    #     if disabled_source_sequences:
    #         log = disable_music(rom, disabled_source_sequences.values(), log)

    #     rebuild_sequences(rom, sequences + fanfare_sequences)
    # else:
    if ootworld.background_music == 'randomized' or bgm_mapped:
        log = shuffle_pointers_table(rom, bgm_ids, music_mapping, log, ootworld.random)

    if ootworld.fanfares == 'randomized' or ff_mapped or ocarina_mapped:
        log = shuffle_pointers_table(rom, ff_ids, music_mapping, log, ootworld.random)
    # end_else
    # End AP modified code
    ########################
    if disabled_target_sequences:
        log = disable_music(rom, disabled_target_sequences.values(), log)

    return log, errors

# Update the original file to use the modified function
OoTRMusic.randomize_music = randomize_music
