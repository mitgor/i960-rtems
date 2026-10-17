#!/usr/bin/env python3
"""One guarded op-12 live vector/timer-mode observation with full audits."""
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

BDF, OLD = '0000:37:09.1', '0000:37:04.1'
IMAGE_SHA = '93faf91f553822665cd4125d90b1066370c4bca0da76af8336daf98bc2dae094'
MODULE_SHA = 'a4309b14e1a5cb36558b1bb96c267f251e9974603beffbddc4ee2188f931a280'
HANDLER_SHA = 'dd4d51c24ef1debcbc1dc4830c0761696be94849082965146445f38e2662c52f'
NONCE, MAGIC = 0x161610c1, 0x31434556
FIRST, LAST = 0x980, 0x9c8
DEBUG = Path('/sys/kernel/debug/accele-vector')
DEVICE = Path('/sys/bus/pci/devices') / BDF

def sha(data): return hashlib.sha256(data).hexdigest()
def need(ok, reason):
    if not ok: raise RuntimeError(reason)
def fields(path): return dict(part.split('=', 1) for part in path.read_text().split())
def put(path, obj): path.write_text(json.dumps(obj, indent=2) + '\n')

def verify_read(path, boot, card, old):
    req = json.loads((path / 'request.json').read_text())
    result = json.loads((path / 'result.json').read_text())
    status = fields(path / 'status.txt')
    data = (path / 'data.bin').read_bytes()
    need(req['boot_id'] == boot and req['selector'] == 9 and
         req['length'] == len(data) == 1048576 and
         sha(data) == result['sha256'] == IMAGE_SHA and
         result['card_after'] == card and result['old_after'] == old and
         all(status.get(k) == '0' for k in ('status', 'residual', 'guard_changes')),
         f'full flash read failed: {path}')

def decode(page):
    w = struct.unpack_from('<18I', page, FIRST)
    need(w[0] == MAGIC and w[1] == NONCE and w[2] in (0, 3, 7), 'report header')
    need(w[3] == w[16] and w[4] == w[17], 'cached vector changed')
    report = dict(flags=w[2], cached_vector18=f'0x{w[3]:08x}',
                  cached_vector130=f'0x{w[4]:08x}',
                  pre=dict(ipnd=f'0x{w[5]:08x}', imsk=f'0x{w[6]:08x}',
                           imap2=f'0x{w[7]:08x}', trr1=f'0x{w[8]:08x}',
                           tcr1=f'0x{w[9]:08x}'),
                  mode=(f'0x{w[10]:08x}' if w[2] else None),
                  post=dict(ipnd=f'0x{w[11]:08x}', imsk=f'0x{w[12]:08x}',
                            imap2=f'0x{w[13]:08x}', trr1=f'0x{w[14]:08x}',
                            tcr1=f'0x{w[15]:08x}'))
    if w[2]:
        need(w[8] == w[9] == 0 and not (w[5] & 0x2000) and
             not (w[6] & 0x2000) and not (w[7] & 0xf00000),
             'mode read without idle/masked prerequisite')
        need(w[8] == w[14] and w[9] == w[15] and
             not (w[11] & 0x2000) and not (w[12] & 0x2000) and
             not (w[13] & 0xf00000), 'timer changed after mode read')
        need(bool(w[2] & 4) == bool(w[10] & 1), 'TC flag discrepancy')
    else:
        need(w[10] == 0xffffffff, 'skipped mode was nevertheless read')
    return report

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('module', 'handler', 'image', 'readback0', 'readback1', 'out'):
        p.add_argument('--' + name.replace('_', '-'), type=Path, required=True)
    a = p.parse_args()
    lock = open('/run/lock/i960-loadrun.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    need(sha(a.module.read_bytes()) == MODULE_SHA, 'wrong command module')
    handler = a.handler.read_bytes()
    need(len(handler) == 3868 and sha(handler) == HANDLER_SHA,
         'wrong linked handler')
    need(sha(a.image.read_bytes()) == IMAGE_SHA, 'wrong flash image')
    need(not DEBUG.exists() and not Path('/sys/module/vector_command').exists(),
         'previous command retained')
    card = select(BDF, 'accele160', driver='myrsread')
    old = select(OLD, 'dac960pg')
    need(old['driver'] is None, 'old card bound')
    need(not list(DEVICE.glob('host*/target*/*/block/*')), 'block device present')
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
    need(original == 0xc0000000, 'unexpected PIATVR')
    def translate(address):
        cfg.seek(0x44); cfg.write(struct.pack('<I', address)); cfg.seek(0x44)
        need(struct.unpack('<I', cfg.read(4))[0] == address, 'PIATVR readback')
    def snap(address):
        translate(address)
        return bytes(bar[4096:8192])
    def write(address, offset, data):
        translate(address)
        bar[4096 + offset:4096 + offset + len(data)] = data
        need(bytes(bar[4096 + offset:4096 + offset + len(data)]) == data,
             'PCI aperture writeback')
    try:
        before = snap(0xc000e000)
        owner = snap(0xc0384000)
        (a.out / 'page-before.bin').write_bytes(before)
        (a.out / 'owner-before.bin').write_bytes(owner)
        prefix = handler[0xf000 - 0xe1d8:]
        need(before == prefix + b'\xff' * (4096 - len(prefix)),
             'loader page does not match exact code tail and erased report area')
        translate(original)
        subprocess.run(['insmod', str(a.module), 'bdf=' + BDF], check=True)
        need(fields(DEBUG / 'status').get('started') == '0', 'unexpected module state')
        (DEBUG / 'start').write_text('probe\n')
        began = time.monotonic()
        while time.monotonic() - began < 5:
            state = fields(DEBUG / 'status')
            if state.get('done') == '1': break
            time.sleep(.01)
        (a.out / 'status.txt').write_text((DEBUG / 'status').read_text())
        need(state.get('done') == '1' and state.get('status') == '0' and
             state.get('residual') == '0', 'callback uncertain; retain module')
        page = snap(0xc000e000)
        after_owner = snap(0xc0384000)
        (a.out / 'page-after.bin').write_bytes(page)
        (a.out / 'owner-after.bin').write_bytes(after_owner)
        need(page[:FIRST] == before[:FIRST] and page[LAST:] == before[LAST:],
             'loader page changed outside bounded report')
        need(after_owner[0x2a0:0xaa0] == owner[0x2a0:0xaa0],
             'allocator owner records changed')
        report = decode(page)
        write(0xc000e000, FIRST, before[FIRST:LAST])
        need(snap(0xc000e000) == before, 'loader page restoration')
        translate(original)
        (DEBUG / 'release').write_text('release\n')
        need(fields(DEBUG / 'status').get('released') == '1', 'release failed')
        subprocess.run(['rmmod', 'vector_command'], check=True)
        put(a.out / 'result.json', dict(boot_id=boot,
            elapsed_s=round(time.monotonic() - began, 6), report=report,
            owner_records_unchanged=True, page_restored=True,
            card_after=select(BDF, 'accele160'), old_after=select(OLD, 'dac960pg')))
        print(json.dumps(report, indent=2))
    finally:
        translate(original)
        bar.close(); res.close(); cfg.close()

if __name__ == '__main__': main()
