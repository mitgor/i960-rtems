#!/usr/bin/env python3
"""Ask UPD1 to hash its 1 MiB flash, then abort the RAM session.

This sends only BEGIN (1) and ABORT (4). It never stages an image or sends
APPLY (5). A matching digest is card-computed evidence, not host byte readback.
"""
import argparse
import fcntl
import json
import mmap
import os
from pathlib import Path
import struct
import time

DEVICE = Path('/sys/bus/pci/devices/0000:37:09.1')
PEER = Path('/sys/bus/pci/devices/0000:37:04.1')
DEFAULT = 0xc0000000
CONTROL = 0xc0800000
MAGIC = 0x31445055


def read32(fd, offset):
    return struct.unpack('<I', os.pread(fd, 4, offset))[0]


def command(bar, seq, number, timeout):
    def word(index):
        return struct.unpack_from('<I', bar, 0x1000 + 4 * index)[0]

    def put(index, value):
        struct.pack_into('<I', bar, 0x1000 + 4 * index, value)

    if word(1) != seq - 1 or word(2) != seq - 1:
        raise RuntimeError('UPD1 sequence is not idle')
    put(3, number)
    put(4, 0)
    put(5, 0)
    put(6, 0)
    put(1, seq)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if word(2) == seq:
            return {'result': word(7), 'state': word(8), 'next_chunk': word(9),
                    'sequence': word(1), 'acknowledged': word(2)}
        time.sleep(0.05)
    raise TimeoutError(f'UPD1 command {number} did not acknowledge; outcome uncertain')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--boot-id', required=True)
    p.add_argument('--expected-sha256', required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    digest = bytes.fromhex(a.expected_sha256)
    if len(digest) != 32 or a.out.exists():
        raise ValueError('expected 32-byte SHA-256 and new output path')
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    if boot != a.boot_id or PEER.exists() or not DEVICE.exists() or (DEVICE / 'driver').exists():
        raise RuntimeError('boot, sole-card, or unbound-driver gate failed')
    lock = os.open('/run/lock/i960-loadrun.lock', os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    cfg = os.open(DEVICE / 'config', os.O_RDWR)
    bar_fd = None
    bar = None
    result = {'boot_id': boot, 'expected_sha256': digest.hex(),
              'commands': [], 'flash_writes': 0, 'bar_data_writes': 0}
    original = None
    try:
        if os.pread(cfg, 4, 0) != bytes.fromhex('69105000'):
            raise RuntimeError('unexpected PCI identity')
        original = read32(cfg, 0x44)
        if original != DEFAULT:
            raise RuntimeError('unexpected PIATVR baseline')
        bar_fd = os.open(DEVICE / 'resource0', os.O_RDWR | os.O_SYNC)
        bar = mmap.mmap(bar_fd, 0x2000, access=mmap.ACCESS_WRITE)
        os.pwrite(cfg, struct.pack('<I', CONTROL), 0x44)
        if read32(cfg, 0x44) != CONTROL:
            raise RuntimeError('PIATVR remap failed')

        def word(index):
            return struct.unpack_from('<I', bar, 0x1000 + 4 * index)[0]

        if word(0) != MAGIC or word(10) != 2 or word(1) != word(2) or word(8) != 0 or word(9) != 0:
            raise RuntimeError('UPD1 absent or not idle')
        if word(1) > 0xfffffffd:
            raise RuntimeError('UPD1 sequence exhausted')
        seq = word(1)
        # BEGIN copies the flash array and compares its SHA-256 to these bytes.
        # The target digest is immaterial until CHUNK/SEAL, which are excluded.
        for start in (128, 160):
            for offset in range(0, 32, 4):
                struct.pack_into('<I', bar, 0x1000 + start + offset,
                                 struct.unpack_from('<I', digest, offset)[0])
        begin = command(bar, seq + 1, 1, 90)
        result['commands'].append({'name': 'BEGIN', **begin})
        if begin['result'] != 0 or begin['state'] != 1 or begin['next_chunk'] != 0:
            raise RuntimeError(f'flash digest rejected: {begin}')
        abort = command(bar, seq + 2, 4, 30)
        result['commands'].append({'name': 'ABORT', **abort})
        if abort['result'] != 0 or abort['state'] != 0 or abort['next_chunk'] != 0:
            raise RuntimeError(f'RAM session did not abort: {abort}')
        result['card_digest_matched'] = True
    finally:
        if original == DEFAULT:
            os.pwrite(cfg, struct.pack('<I', original), 0x44)
            result['piatvr_restored'] = read32(cfg, 0x44) == original
            result['pci_identity_after'] = os.pread(cfg, 8, 0).hex()
        if bar is not None:
            bar.close()
        if bar_fd is not None:
            os.close(bar_fd)
        os.close(cfg)
        os.close(lock)
        a.out.write_text(json.dumps(result, indent=2) + '\n')
    if not result.get('piatvr_restored') or result.get('pci_identity_after', '')[:8] != '69105000':
        raise RuntimeError('PIATVR or PCI identity not restored')
    print(a.out)


if __name__ == '__main__':
    main()
