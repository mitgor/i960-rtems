#!/usr/bin/env python3
"""Read-only survey of every PCI-addressable odd upper-bank DRAM page."""
import argparse
import fcntl
import hashlib
import json
import mmap
import struct
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'host/accele160/lease_probe'))
from run_lease import BDF, OLD, PAGE, DEVICE, need, verify_read
sys.path.insert(0, str(ROOT/'rtems/transport'))
from card_select import select


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--readback0', type=Path, required=True)
    parser.add_argument('--readback1', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    lock = open('/run/lock/i960-loadrun.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    card = select(BDF, 'accele160', driver='myrsread')
    old = select(OLD, 'dac960pg')
    need(old['driver'] is None, 'old card bound')
    host, = DEVICE.glob('host*/scsi_host/host*')
    need((host/'stock_descriptor').read_text().startswith('state=0 '),
         'stock descriptor active')
    need(not list(DEVICE.glob('host*/target*/*/block/*')), 'block device')
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    for path in (args.readback0, args.readback1):
        verify_read(path, boot, card, old)
    args.out.mkdir(parents=True, exist_ok=False)
    cfg = (DEVICE/'config').open('r+b', buffering=0)
    res = (DEVICE/'resource0').open('r+b', buffering=0)
    bar = mmap.mmap(res.fileno(), 2*PAGE)
    cfg.seek(0x44)
    original = struct.unpack('<I', cfg.read(4))[0]
    need(original == 0xc0000000, 'unexpected PIATVR')

    def snap(base):
        cfg.seek(0x44)
        cfg.write(struct.pack('<I', base))
        cfg.seek(0x44)
        need(struct.unpack('<I', cfg.read(4))[0] == base, 'PIATVR readback')
        return bytes(bar[PAGE:2*PAGE])

    try:
        owner_before = snap(0xc0384000)
        records = []
        nonzero = bytearray()
        saved = 0
        for index in range(1, 2048, 2):
            address = 0xc0800000 + index*PAGE
            page = snap(address-PAGE)
            offsets = [i for i, value in enumerate(page) if value]
            item = dict(index=index, address=f'0x{address:08x}',
                        sha256=hashlib.sha256(page).hexdigest(),
                        nonzero_bytes=len(offsets))
            if offsets:
                item['first_offset'] = offsets[0]
                item['last_offset'] = offsets[-1]
                nonzero.append(1)
                if saved < 16:
                    (args.out/f'page-{index:04d}.bin').write_bytes(page)
                    saved += 1
            else:
                nonzero.append(0)
            records.append(item)
        need(snap(0xc0384000)[0x2a0:0xaa0] ==
             owner_before[0x2a0:0xaa0], 'allocator records changed')
        (args.out/'nonzero-bitmap.bin').write_bytes(nonzero)
        (args.out/'survey.json').write_text(json.dumps(dict(
            boot_id=boot, card=card, old=old, pages=records,
            nonzero_pages=sum(nonzero),
            nonzero_pages_saved=saved,
            preflight=[str(args.readback0),str(args.readback1)]),
            indent=2)+'\n')
    finally:
        cfg.seek(0x44)
        cfg.write(struct.pack('<I', original))
        cfg.seek(0x44)
        need(struct.unpack('<I', cfg.read(4))[0] == original,
             'PIATVR restoration')
        bar.close()
        res.close()
        cfg.close()


if __name__ == '__main__':
    main()
