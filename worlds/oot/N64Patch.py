import zlib
import copy

from .OoTR.N64Patch import write_block
from .OoTR.ntype import BigStream

# This will create the patch file. Which can be applied to a source rom.
# xor_range is the range the XOR key will read from. This range is not
# too important, but I tried to choose from a section that didn't really
# have big gaps of 0s which we want to avoid.
def get_patch_data(rom, rand, xor_range=(0x00B8AD30, 0x00F029A0)):
    """
    Modified version of OoTR's `create_patch_file`. Instead of writing the patch
    data to a file, the data is returned. Also uses the world's randomization
    object instead of Python's `random` module
    """
    dma_start, dma_end = rom.get_dma_table_range()

    # add header
    patch_data = BigStream([])
    patch_data.append_bytes(list(map(ord, 'ZPFv1')))
    patch_data.append_int32(dma_start)
    patch_data.append_int32(xor_range[0])
    patch_data.append_int32(xor_range[1])

    # get random xor key. This range is chosen because it generally
    # doesn't have many sections of 0s
    xor_address = rand.randint(*xor_range)
    patch_data.append_int32(xor_address)

    new_buffer = copy.copy(rom.original.buffer)

    # write every changed DMA entry
    for dma_index, (from_file, start, size) in rom.changed_dma.items():
        patch_data.append_int16(dma_index)
        patch_data.append_int32(from_file)
        patch_data.append_int32(start)
        patch_data.append_int24(size)

        # We don't trust files that have modified DMA to have their
        # changed addresses tracked correctly, so we invalidate the
        # entire file
        for address in range(start, start + size):
            rom.changed_address[address] = rom.buffer[address]

        # Simulate moving the files to know which addresses have changed
        if from_file >= 0:
            old_dma_start, old_dma_end, old_size = rom.original.get_dmadata_record_by_key(from_file)
            copy_size = min(size, old_size)
            new_buffer[start:start+copy_size] = rom.original.read_bytes(from_file, copy_size)
            new_buffer[start+copy_size:start+size] = [0] * (size - copy_size)
        else:
            # this is a new file, so we just fill with null data
            new_buffer[start:start+size] = [0] * size

    # end of DMA entries
    patch_data.append_int16(0xFFFF)

    # filter down the addresses that will actually need to change.
    # Make sure to not include any of the DMA table addresses
    changed_addresses = [address for address,value in rom.changed_address.items() \
        if (address >= dma_end or address < dma_start) and \
            (address in rom.force_patch or new_buffer[address] != value)]
    changed_addresses.sort()

    # Write the address changes. We'll store the data with XOR so that
    # the patch data won't be raw data from the patched rom.
    data = []
    block_start = None
    BLOCK_HEADER_SIZE = 7 # this is used to break up gaps
    for address in changed_addresses:
        # if there's a block to write and there's a gap, write it
        if block_start:
            block_end = block_start + len(data) - 1
            if address > block_end + BLOCK_HEADER_SIZE:
                xor_address = write_block(rom, xor_address, xor_range, block_start, data, patch_data)
                data = []
                block_start = None
                block_end = None

        # start a new block
        if not block_start:
            block_start = address
            block_end = address - 1

        # save the new data
        data += rom.buffer[block_end+1:address+1]

    # if there was any left over blocks, write them out
    if block_start:
        xor_address = write_block(rom, xor_address, xor_range, block_start, data, patch_data)

    # compress the patch file
    patch_data = bytes(patch_data.buffer)
    patch_data = zlib.compress(patch_data)

    return patch_data
