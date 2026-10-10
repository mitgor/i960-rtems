"""BIO1 wire format; paired with loader/runtime/buffer_io.h."""
import struct
OFFSET = 0x8000
BASE = 0xc0f34000
HEADER = 64
INPUT_MAX = 4096
GUARD1 = HEADER + INPUT_MAX
OUTPUT = GUARD1 + 16
OUTPUT_MAX = 8192
GUARD2 = OUTPUT + OUTPUT_MAX
SIZE = GUARD2 + 16
IMAGE_SIZE = OFFSET + SIZE
MAGIC = 0x314f4942
PENDING = 0xffffffff

def prepare(code, incoming, capacity, sequence, entry=0):
    if not 0 < len(code) <= OFFSET or len(code) % 4 or entry % 4 or not 0 <= entry < len(code):
        raise ValueError('buffer code must be aligned, at most 32 KiB, with entry inside code')
    if len(incoming) > INPUT_MAX or not 0 <= capacity <= OUTPUT_MAX or not 0 < sequence <= 0xffffffff:
        raise ValueError('invalid input length, output capacity or sequence')
    block = bytearray(SIZE)
    struct.pack_into('<8I', block, 0, MAGIC, 1, sequence, len(incoming), capacity, PENDING, 0, 0)
    block[HEADER:HEADER+len(incoming)] = incoming
    block[GUARD1:GUARD1+16] = b'\xa5'*16
    block[OUTPUT:GUARD2] = b'\xcc'*OUTPUT_MAX
    block[GUARD2:] = b'\x5a'*16
    return code.ljust(OFFSET,b'\0') + block

def response(before, after):
    if len(before) != 524288 or len(after) != len(before):
        raise ValueError('response image length mismatch')
    fields = struct.unpack_from('<8I', after, OFFSET)
    magic, version, sequence, incoming, capacity, status, length, reply = fields
    original = struct.unpack_from('<8I', before, OFFSET)
    if (original[:2] != (MAGIC,1) or not original[2] or original[3]>INPUT_MAX or
        original[4]>OUTPUT_MAX or original[5:] != (PENDING,0,0) or
        fields[:5] != original[:5] or status == PENDING or reply != sequence or
        length > capacity or (status and length)):
        raise ValueError('invalid, stale or oversized BIO1 response')
    normalized = bytearray(after)
    normalized[OFFSET+20:OFFSET+32] = before[OFFSET+20:OFFSET+32]
    start = OFFSET+OUTPUT
    normalized[start:start+length] = before[start:start+length]
    if normalized != before:
        raise ValueError('program modified immutable bytes or output guards')
    return status, after[start:start+length]
