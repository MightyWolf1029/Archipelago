from .OoTR.SceneFlags import get_alt_list_bytes, get_collectible_flag_table, get_collectible_flag_table_bytes

def get_collectible_flag_addresses(world, collectible_scene_flags_table):
    """
    Retrieve address + bit for each item.
    Based on `get_collectible_flag_offset` in the C code.
    """

    def get_collectible_flag_offset(scene: int, room: int, setup_id: int) -> int:
        """Ported directly from `get_items.c`"""

        num_scenes = collectible_scene_flags_table[0]
        index = 1
        scene_id = 0
        room_id = 0
        room_setup_count = 0
        room_byte_offset = 0
        # Loop through collectible_scene_flags_table until we find the right scene
        while num_scenes > 0:
            scene_id = collectible_scene_flags_table[index]
            room_setup_count = collectible_scene_flags_table[index+1]
            index += 2
            if scene_id == scene:  # found the scene
                # Loop through each room/setup combination until we find the right one.
                for i in range(room_setup_count):
                    room_id = collectible_scene_flags_table[index] & 0x3F
                    setup_id_temp = (collectible_scene_flags_table[index] & 0xC0) >> 6
                    room_byte_offset = (collectible_scene_flags_table[index+1] << 8) + collectible_scene_flags_table[index+2]
                    index += 3
                    if room_id == room and setup_id_temp == setup_id:
                        return room_byte_offset
            else:  # Not the right scene, skip to the next one
                index += 3 * room_setup_count
            num_scenes -= 1
        return -1

    collectible_flag_addresses = {}
    for location in world.get_locations():
        if location.type in ["Freestanding", "Pot", "FlyingPot", "Crate", "SmallCrate", "Beehive", "RupeeTower"]:
            default = location.default
            if isinstance(default, list):
                default = default[0]
            room, setup, flag = default
            offset = get_collectible_flag_offset(location.scene, room, setup)
            item_id = location.address
            collectible_flag_addresses[item_id] = [offset, flag]
    return collectible_flag_addresses
