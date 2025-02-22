from .OoTR.TextBox import *
#from .OoTR import TextBox as OoTRTextBox
#from . import Messages

# Overwrite OoTR TextBox's messages with our patched version
#OoTRTextBox.Messages = Messages

rom_safe_lambda = lambda c: c if c in character_table else '?'
def rom_safe_text(text):
    return ''.join(map(rom_safe_lambda, text))