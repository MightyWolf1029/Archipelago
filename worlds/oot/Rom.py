import threading
from Utils import user_path
from .OoTR.Utils import __version__
from .OoTR.Rom import *
from .OoTR import Rom as OoTRRom

double_cache_prevention = threading.Lock()

class Rom(OoTRRom.Rom):
    """
    Modified implementation of `Rom`'s `Rom` class. Changes
    `original` to a class variable instead of an instance variable,
    and updates `__init__` and `decompress_rom_file`.
    """
    original = None

    def __init__(self, file=None, force_use=False):
        """
        Modified implementation of `Rom`'s `__init__` function.
        """
        # Directly call BigStream's __init__ function, since we're overwriting OoTR's __init__
        BigStream.__init__(self, [])

        self.changed_address = {}
        self.changed_dma = {}
        self.force_patch = []

        if file is None:
            return

        decomp_file = user_path('ZOOTDEC.z64')

        with open(data_path('generated/symbols.json'), 'r') as stream:
            symbols = json.load(stream)
            self.symbols = { name: int(addr, 16) for name, addr in symbols.items() }

        # If decompressed file already exists, read from it
        if not force_use:
            if os.path.exists(decomp_file):
                file = decomp_file

            if file == '':
                # if not specified, try to read from the previously decompressed rom
                file = decomp_file
                try:
                    self.read_rom(file)
                except FileNotFoundError:
                    # could not find the decompressed rom either
                    raise FileNotFoundError('Must specify path to base ROM')
            else:
                self.read_rom(file)
        else:
            self.read_rom(file)

        # decompress rom, or check if it's already decompressed
        self.decompress_rom_file(file, decomp_file, force_use)

        # Add file to maximum size
        self.buffer.extend(bytearray([0x00] * (0x4000000 - len(self.buffer))))
        with double_cache_prevention:
            if not self.original:
                Rom.original = self.copy()

        # Add version number to header.
        self.write_bytes(0x35, get_version_bytes(__version__))
        self.force_patch.extend([0x35, 0x36, 0x37])

    def decompress_rom_file(self, file, decomp_file, skip_crc_check):
        """
        Modified implementation of `Rom`'s `decompress_rom_file` function.
        """
        validCRC = [
            [0xEC, 0x70, 0x11, 0xB7, 0x76, 0x16, 0xD7, 0x2B], # Compressed
            [0x70, 0xEC, 0xB7, 0x11, 0x16, 0x76, 0x2B, 0xD7], # Byteswap compressed
            [0x93, 0x52, 0x2E, 0x7B, 0xE5, 0x06, 0xD4, 0x27], # Decompressed
        ]

        # Validate ROM file
        file_name = os.path.splitext(file)
        romCRC = list(self.buffer[0x10:0x18])
        if romCRC not in validCRC and not skip_crc_check:
            # Bad CRC validation
            raise RuntimeError('ROM file %s is not a valid OoT 1.0 US ROM.' % file)
        elif len(self.buffer) < 0x2000000 or len(self.buffer) > (0x4000000) or file_name[1].lower() not in ['.z64', '.n64']:
            # ROM is too big, or too small, or not a bad type
            raise RuntimeError('ROM file %s is not a valid OoT 1.0 US ROM.' % file)
        elif len(self.buffer) == 0x2000000:
            # If Input ROM is compressed, then Decompress it

            sub_dir = data_path("Decompress")

            if platform.system() == 'Windows':
                subcall = [sub_dir + "\\Decompress.exe", file, decomp_file]
            elif platform.system() == 'Linux':
                if platform.uname()[4] == 'aarch64' or platform.uname()[4] == 'arm64':
                    subcall = [sub_dir + "/Decompress_ARM64", file, decomp_file]
                else:
                    subcall = [sub_dir + "/Decompress", file, decomp_file]
            elif platform.system() == 'Darwin':
                subcall = [sub_dir + "/Decompress.out", file, decomp_file]
            else:
                raise RuntimeError('Unsupported operating system for decompression. Please supply an already decompressed ROM.')

            if not os.path.exists(subcall[0]):
                raise RuntimeError(f'Decompressor does not exist! Please place it at {subcall[0]}.')
            subprocess.call(subcall, **subprocess_args())
            self.read_rom(decomp_file)
        else:
            # ROM file is a valid and already uncompressed
            pass

# Patch OoTR's Rom class with our modified Rom class
OoTRRom.Rom = Rom

# Used by OoTAdjuster and OoTClient
def compress_rom_file(input_file, output_file):
    compressor_path = "."

    if platform.system() == 'Windows':
        executable_path = "Compress.exe"
    elif platform.system() == 'Linux':
        if platform.uname()[4] == 'aarch64' or platform.uname()[4] == 'arm64':
            executable_path = "Compress_ARM64"
        else:
            executable_path = "Compress"
    elif platform.system() == 'Darwin':
        executable_path = "Compress.out"
    else:
        raise RuntimeError('Unsupported operating system for compression.')
    compressor_path = os.path.join(compressor_path, executable_path)
    if not os.path.exists(compressor_path):
        raise RuntimeError(f'Compressor does not exist! Please place it at {compressor_path}.')
    import logging
    logging.info(subprocess.check_output([compressor_path, input_file, output_file],
                                             **subprocess_args(include_stdout=False)))
