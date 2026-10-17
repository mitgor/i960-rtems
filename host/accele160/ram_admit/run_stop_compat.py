#!/usr/bin/env python3
"""Retest accepted operation 11 on the new operation-13 firmware image."""
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
IMAGE_SHA = '1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
MODULE_SHA = 'cfad41dfd8465f51243467234fd71ae0f658aa778ed318dc674257ff38720a59'
HANDLER_SHA = '8d8c79c3b8c206608ef7221000991c0d75eb101ce06581fedc2a74522648ad34'
DEBUG = Path('/sys/kernel/debug/accele-stop')
DEVICE = Path('/sys/bus/pci/devices') / BDF
FIRST, LAST = 0x960, 0x980
MAGIC, NONCE, EPOCH = 0x31504f54, 0x161610b1, 1
READY, STOP, ACK, TIME = 0x59444152, 0x504f5453, 0x214b4341, 0x454d4954

def sha(data): return hashlib.sha256(data).hexdigest()
def need(ok, reason):
    if not ok: raise RuntimeError(reason)
def fields(path): return dict(part.split('=', 1) for part in path.read_text().split())
def put(path, obj): path.write_text(json.dumps(obj, indent=2) + '\n')

def verify_read(path, boot, card, old):
    request = json.loads((path / 'request.json').read_text())
    result = json.loads((path / 'result.json').read_text())
    status = fields(path / 'status.txt')
    data = (path / 'data.bin').read_bytes()
    need(request['boot_id'] == boot and request['selector'] == 9 and
         request['length'] == len(data) == 1048576 and
         sha(data) == result['sha256'] == IMAGE_SHA and
         result['card_after'] == card and result['old_after'] == old and
         all(status.get(key) == '0' for key in ('status', 'residual', 'guard_changes')),
         f'full flash read failed: {path}')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('module', 'handler', 'image', 'readback0', 'readback1', 'out'):
        p.add_argument('--' + name.replace('_', '-'), type=Path, required=True)
    a = p.parse_args()
    lock = open('/run/lock/i960-loadrun.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    need(sha(a.module.read_bytes()) == MODULE_SHA, 'wrong one-shot command module')
    handler = a.handler.read_bytes()
    need(len(handler) == 4324 and sha(handler) == HANDLER_SHA,
         'wrong linked handler')
    need(sha(a.image.read_bytes()) == IMAGE_SHA, 'wrong persistent image')
    need(not DEBUG.exists() and not Path('/sys/module/stop_command').exists(),
         'prior STOP companion retained')
    card = select(BDF, 'accele160', driver='myrsread')
    old = select(OLD, 'dac960pg')
    need(old['driver'] is None, 'old card bound')
    need(not list(DEVICE.glob('host*/target*/*/block/*')), 'card has block device')
    host, = DEVICE.glob('host*/scsi_host/host*')
    need((host / 'stock_descriptor').read_text().startswith('state=0 '),
         'stock descriptor active')
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    for path in (a.readback0, a.readback1):
        verify_read(path, boot, card, old)
    a.out.mkdir(parents=True, exist_ok=False)
    put(a.out / 'preflight.json', dict(boot_id=boot, card=card, old_card=old,
        image_sha256=IMAGE_SHA, module_sha256=MODULE_SHA,
        handler_sha256=HANDLER_SHA,
        full_reads=[str(a.readback0), str(a.readback1)]))

    cfg = (DEVICE / 'config').open('r+b', buffering=0)
    res = (DEVICE / 'resource0').open('r+b', buffering=0)
    bar = mmap.mmap(res.fileno(), 8192)
    cfg.seek(0x44)
    original = struct.unpack('<I', cfg.read(4))[0]
    need(original == 0xc0000000, 'unexpected PIATVR before test')
    def translate(address):
        cfg.seek(0x44); cfg.write(struct.pack('<I', address)); cfg.seek(0x44)
        need(struct.unpack('<I', cfg.read(4))[0] == address, 'PIATVR readback')
    def snap(address):
        translate(address)
        return bytes(bar[4096:8192])
    def write(offset, data):
        translate(0xc000e000)
        bar[4096 + offset:4096 + offset + len(data)] = data
        need(bytes(bar[4096 + offset:4096 + offset + len(data)]) == data,
             'sideband PCI write did not read back')
    try:
        before = snap(0xc000e000)
        owner = snap(0xc0384000)
        (a.out / 'page-before.bin').write_bytes(before)
        (a.out / 'owner-before.bin').write_bytes(owner)
        prefix = handler[0xf000 - 0xe1d8:]
        need(before == prefix + b'\xff' * (4096 - len(prefix)),
             'loader page code tail or erased report changed')
        results = []
        for ordinal, mode in enumerate(('stop', 'deadline')):
            record = struct.pack('<4I', MAGIC, NONCE, EPOCH, 0) + b'\xa5' * 16
            write(FIRST, record)
            need(snap(0xc000e000)[FIRST:LAST] == record, 'preloaded record drift')
            translate(original)
            subprocess.run(['insmod', str(a.module), 'bdf=' + BDF], check=True)
            need(fields(DEBUG / 'status').get('started') == '0', 'command already started')
            (DEBUG / 'start').write_text('probe\n')
            began = time.monotonic()
            while time.monotonic() - began < 2:
                current = snap(0xc000e000)
                if struct.unpack_from('<I', current, 0x970)[0] == READY:
                    break
                if fields(DEBUG / 'status').get('done') == '1':
                    break
                time.sleep(.002)
            (a.out / f'run-{ordinal}-ready-page.bin').write_bytes(current)
            (a.out / f'run-{ordinal}-ready-status.txt').write_text((DEBUG / 'status').read_text())
            need(struct.unpack_from('<I', current, 0x970)[0] == READY and
                 fields(DEBUG / 'status').get('done') == '0',
                 'READY missing or callback finished early; retain command')
            stale_pending = None
            if mode == 'stop':
                write(0x96c, struct.pack('<I', 0xdeadbeef))
                time.sleep(.005)
                stale_pending = fields(DEBUG / 'status').get('done') == '0'
                (a.out / f'run-{ordinal}-stale-page.bin').write_bytes(snap(0xc000e000))
                need(stale_pending, 'stale token ended callback; retain command')
                write(0x96c, struct.pack('<I', STOP))
            translate(original)
            while time.monotonic() - began < 35:
                state = fields(DEBUG / 'status')
                if state.get('done') == '1': break
                time.sleep(.01)
            (a.out / f'run-{ordinal}-status.txt').write_text((DEBUG / 'status').read_text())
            need(state.get('done') == '1', 'callback pending; retain command/module')
            page = snap(0xc000e000)
            own = snap(0xc0384000)
            (a.out / f'run-{ordinal}-page.bin').write_bytes(page)
            (a.out / f'run-{ordinal}-owner.bin').write_bytes(own)
            need(page[:FIRST] == before[:FIRST] and page[LAST:] == before[LAST:],
                 'loader page changed outside exact STOP record')
            need(own[0x2a0:0xaa0] == owner[0x2a0:0xaa0], 'allocator records changed')
            words = struct.unpack_from('<8I', page, FIRST)
            if mode == 'stop':
                need(words == (MAGIC, NONCE, EPOCH, STOP, READY, ACK, NONCE, EPOCH),
                     'STOP ACK or echo mismatch')
                need(state.get('status') == state.get('residual') == '0',
                     'STOP callback failed')
            else:
                need(words == (MAGIC, NONCE, EPOCH, 0, TIME, 0xa5a5a5a5,
                               0xa5a5a5a5, 0xa5a5a5a5), 'deadline report mismatch')
                need(state.get('status') == '2' and state.get('residual') == '0',
                     'deadline must return stock unsupported status 2')
            result = dict(mode=mode, elapsed_s=round(time.monotonic() - began, 6),
                          status=state, stale_pending=stale_pending,
                          owner_records_unchanged=True,
                          other_owner_page_diffs=[i for i, (x, y) in enumerate(zip(owner, own))
                             if x != y and not 0x2a0 <= i < 0xaa0])
            results.append(result)
            write(FIRST, before[FIRST:LAST])
            need(snap(0xc000e000) == before, 'loader page restoration failed')
            translate(original)
            (DEBUG / 'release').write_text('release\n')
            need(fields(DEBUG / 'status').get('released') == '1', 'module release failed')
            subprocess.run(['rmmod', 'stop_command'], check=True)
        need(snap(0xc000e000) == before and
             snap(0xc0384000)[0x2a0:0xaa0] == owner[0x2a0:0xaa0],
             'final page/owner state differs')
        translate(original)
        put(a.out / 'result.json', dict(boot_id=boot, runs=results,
            page_restored=True, owner_records_unchanged=True,
            card_after=select(BDF, 'accele160'), old_after=select(OLD, 'dac960pg')))
        print(json.dumps(results, indent=2))
    finally:
        translate(original)
        bar.close(); res.close(); cfg.close()

if __name__ == '__main__': main()
