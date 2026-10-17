#!/usr/bin/env python3
"""Run two exact read-only 80303 inventories with full flash/owner audits."""
import argparse
import fcntl
import hashlib
import json
import mmap
from pathlib import Path
import struct
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'rtems/transport'))
from card_select import select

BDF = '0000:37:09.1'
OLD = '0000:37:04.1'
IMAGE_SHA = '9d5d4da2c283d10e1dee9c71ceb477f36e389cd0d0548764a3cc5f8a41a24c49'
MODULE_SHA = 'e3bf8856c0746f80305b8d9668e70ff85bd14eb431556d8e2b6a54aa83402333'
NONCE = 0x161610a1
MAGIC = 0x31564e49
ADDRESSES = [0xff000300, 0xff000304, 0xff000310, 0xff000314,
             0xff008500, 0xff008504, 0xff008510, 0xff008520,
             0xff008524, 0xff008528, 0xff008700, 0xff008704,
             0xff008708, 0xff008710, 0x3c]
FIRST = 0x8a0
LAST = FIRST + 16 + len(ADDRESSES) * 8 + 8 * 4
DEBUG = Path('/sys/kernel/debug/accele-inventory')
DEVICE = Path('/sys/bus/pci/devices') / BDF

def sha(data): return hashlib.sha256(data).hexdigest()
def need(ok, message):
    if not ok: raise RuntimeError(message)
def fields(path): return dict(item.split('=', 1) for item in path.read_text().split())

def verify_full_read(directory, boot, card, old):
    request = json.loads((directory / 'request.json').read_text())
    result = json.loads((directory / 'result.json').read_text())
    status = fields(directory / 'status.txt')
    data = (directory / 'data.bin').read_bytes()
    need(request['boot_id'] == boot and request['selector'] == 9 and
         request['length'] == 1048576 and result['sha256'] == IMAGE_SHA and
         len(data) == 1048576 and sha(data) == IMAGE_SHA and
         result['card_after'] == card and result['old_after'] == old and
         all(status.get(key) == '0' for key in ('status', 'residual', 'guard_changes')),
         f'full guarded flash read failed: {directory}')

def decode(page):
    words = struct.unpack_from('<42I', page, FIRST)
    need(words[:4] == (MAGIC, NONCE, len(ADDRESSES), 8), 'inventory header')
    pairs = list(zip(words[4:34:2], words[5:34:2]))
    need([address for address, _ in pairs] == ADDRESSES, 'inventory register list')
    return {'registers': {f'0x{addr:08x}': f'0x{value:08x}' for addr, value in pairs},
            'live_prcb_matches_stock_ibr': pairs[10][1] == 0xfeffdd20,
            'stock_prcb_words': [f'0x{value:08x}' for value in words[34:42]]}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('module', 'image', 'readback0', 'readback1', 'out'):
        p.add_argument('--' + name.replace('_', '-'), type=Path, required=True)
    a = p.parse_args()
    lock = open('/run/lock/i960-loadrun.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    need(sha(a.module.read_bytes()) == MODULE_SHA, 'wrong command module')
    need(sha(a.image.read_bytes()) == IMAGE_SHA, 'wrong firmware image')
    need(not DEBUG.exists() and not Path('/sys/module/inventory_command').exists(), 'prior companion retained')
    card = select(BDF, 'accele160', driver='myrsread')
    old = select(OLD, 'dac960pg')
    need(old['driver'] is None, 'old card bound')
    need(not list(DEVICE.glob('host*/target*/*/block/*')), 'new card has block device')
    host, = DEVICE.glob('host*/scsi_host/host*')
    need((host / 'stock_descriptor').read_text().startswith('state=0 '), 'stock descriptor active')
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    for directory in (a.readback0, a.readback1):
        verify_full_read(directory, boot, card, old)
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / 'preflight.json').write_text(json.dumps(dict(boot_id=boot, card=card,
        old_card=old, image_sha256=IMAGE_SHA, module_sha256=MODULE_SHA,
        full_reads=[str(a.readback0), str(a.readback1)]), indent=2) + '\n')

    cfg = (DEVICE / 'config').open('r+b', buffering=0)
    res = (DEVICE / 'resource0').open('r+b', buffering=0)
    bar = mmap.mmap(res.fileno(), 8192)
    cfg.seek(0x44)
    original = struct.unpack('<I', cfg.read(4))[0]
    need(original == 0xc0000000, 'unexpected PIATVR')
    def translate(address):
        cfg.seek(0x44); cfg.write(struct.pack('<I', address)); cfg.seek(0x44)
        need(struct.unpack('<I', cfg.read(4))[0] == address, 'PIATVR readback')
    def snap(address):
        translate(address)
        return bytes(bar[4096:8192])
    def write(address, offset, value):
        translate(address)
        bar[4096 + offset:4096 + offset + len(value)] = value
        need(bytes(bar[4096 + offset:4096 + offset + len(value)]) == value, 'PCI aperture readback')
    try:
        before = snap(0xc000e000)
        owner = snap(0xc0384000)
        (a.out / 'page-before.bin').write_bytes(before)
        (a.out / 'owner-before.bin').write_bytes(owner)
        need(before == b'\xff' * 4096, 'loader report page not erased')
        results = []
        for ordinal in range(2):
            write(0xc000e000, FIRST, b'\xa5' * (LAST - FIRST))
            translate(original)
            subprocess.run(['insmod', str(a.module), 'bdf=' + BDF], check=True)
            need(fields(DEBUG / 'status').get('started') == '0', 'command already started')
            (DEBUG / 'start').write_text('probe\n')
            started = time.monotonic()
            state = {}
            while time.monotonic() - started < 5:
                state = fields(DEBUG / 'status')
                if state.get('done') == '1': break
                time.sleep(.02)
            (a.out / f'run-{ordinal}-status.txt').write_text((DEBUG / 'status').read_text())
            need(state.get('done') == '1' and state.get('status') == '0' and
                 state.get('residual') == '0', 'inventory pending or failed; retain command')
            page = snap(0xc000e000)
            own = snap(0xc0384000)
            (a.out / f'run-{ordinal}-page.bin').write_bytes(page)
            (a.out / f'run-{ordinal}-owner.bin').write_bytes(own)
            need(page[:FIRST] == before[:FIRST] and page[LAST:] == before[LAST:],
                 'loader page drift outside bounded report')
            need(own[0x2a0:0xaa0] == owner[0x2a0:0xaa0], 'allocator owner records drift')
            decoded = decode(page)
            other_diffs = [i for i, (x, y) in enumerate(zip(owner, own))
                           if x != y and not 0x2a0 <= i < 0xaa0]
            results.append(dict(elapsed_s=round(time.monotonic() - started, 6),
                                other_owner_page_diffs=other_diffs, **decoded))
            write(0xc000e000, FIRST, before[FIRST:LAST])
            need(snap(0xc000e000) == before, 'loader page restoration')
            translate(original)
            (DEBUG / 'release').write_text('release\n')
            need(fields(DEBUG / 'status').get('released') == '1', 'command release failed')
            subprocess.run(['rmmod', 'inventory_command'], check=True)
        need(snap(0xc0384000)[0x2a0:0xaa0] == owner[0x2a0:0xaa0] and
             snap(0xc000e000) == before,
             'final state differs')
        translate(original)
        (a.out / 'result.json').write_text(json.dumps(dict(boot_id=boot,
            runs=results, owner_records_unchanged=True, page_restored=True,
            card_after=select(BDF, 'accele160'), old_after=select(OLD, 'dac960pg')), indent=2) + '\n')
        print(json.dumps(results, indent=2))
    finally:
        translate(original)
        bar.close(); res.close(); cfg.close()

if __name__ == '__main__': main()
