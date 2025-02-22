from .OoTR.Messages import *
#from .OoTR import Messages as OoTRMessages

# Add the Archipelago item messages
ITEM_MESSAGES[0x9097] = "\x08You got an \x05\x41Archipelago item\x05\x40!\x01It seems \x05\x41important\x05\x40!"
ITEM_MESSAGES[0x9098] = "\x08You got an \x05\x43Archipelago item\x05\x40!\x01Doesn't seem like it's needed."

#def update_warp_song_text(messages, world):
#    new_world.settings = world
#    OoTRMessages.update_warp_song_text(messages, new_world)

#OoTRMessages.update_warp_song_text = update_warp_song_text
