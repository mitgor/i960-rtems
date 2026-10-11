#!/usr/bin/env python3
"""Shared C8G1 codec, native oracle, and explicitly selected card backend."""
import ctypes
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAGIC = 0x31473843
REPLY_BYTES = 304


def request(op=1, cycles=0, keys=0, ticks=0, seed=0, rom=b''):
    return struct.pack('<6I', MAGIC, op, cycles, keys, ticks, seed) + rom


def decode(data):
    if len(data) != REPLY_BYTES:
        raise ValueError('wrong C8G1 response length')
    magic, status, executed, total, pc, index, delay, sound = struct.unpack('<8I', data[:32])
    if magic != MAGIC or status > 4 or executed > 1000:
        raise ValueError('invalid C8G1 response')
    return dict(status=status, executed=executed, total=total, pc=pc,
                index=index, delay=delay, sound=sound,
                registers=list(data[32:48]), frame=data[48:].hex())


def demo_rom():
    """Original project demo: move a five-row spaceship using 4/6/2/8."""
    ops = [0x601c, 0x610e, 0x6204, 0x6306, 0x6402, 0x6508,
           0x00e0, 0xa000, 0xd015,
           0xe2a1, 0x70ff, 0xe3a1, 0x7001, 0xe4a1, 0x71ff, 0xe5a1, 0x7101,
           0x6602, 0xf615, 0xf607, 0x3600, 0x1226, 0x120c]
    ops[7] = 0xa000 | (0x200 + len(ops) * 2)
    return struct.pack('>' + 'H' * len(ops), *ops) + bytes([0x20, 0x70, 0xf8, 0xa8, 0x88])


class Native:
    def __init__(self, library=HERE / 'build/libchip8.so'):
        self.lib = ctypes.CDLL(str(library))
        self.lib.c8_size.restype = ctypes.c_uint
        self.lib.c8_request.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                       ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint]
        self.lib.c8_request.restype = ctypes.c_uint
        self.state = ctypes.create_string_buffer(self.lib.c8_size())

    def step(self, data):
        incoming = ctypes.create_string_buffer(data)
        outgoing = ctypes.create_string_buffer(REPLY_BYTES)
        rc = self.lib.c8_request(self.state, incoming, len(data), outgoing, REPLY_BYTES)
        if rc:
            raise ValueError(f'C8G1 request rejected: {rc}')
        return outgoing.raw

    def close(self):
        pass


def card_backend(payload, module, output):
    # Imports only on explicit card selection. Board owns the existing exclusive
    # lock, paired image audits and full restoration; never stop another owner.
    import sys
    sys.path.insert(0, str(HERE.parents[1] / 'rtems/transport'))
    from run import Board
    return Board(payload, module, output)
