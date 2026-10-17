#!/usr/bin/env python3
"""Replay full-image, sideband STOP, deadline and owner captures offline."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from run_stop import (IMAGE_SHA, MODULE_SHA, FIRST, LAST, MAGIC, NONCE, EPOCH,
                      READY, STOP, ACK, TIME, fields)

PREVIOUS_SHA = '9d5d4da2c283d10e1dee9c71ceb477f36e389cd0d0548764a3cc5f8a41a24c49'

def check(ok, message):
    if not ok: raise ValueError(message)
def sha(data): return hashlib.sha256(data).hexdigest()

def readback(path, expected, boot=None):
    request = json.loads((path / 'request.json').read_text())
    result = json.loads((path / 'result.json').read_text())
    status = fields(path / 'status.txt')
    data = (path / 'data.bin').read_bytes()
    check(request['selector'] == 9 and request['length'] == len(data) == 1048576,
          'read request/length')
    check(boot is None or request['boot_id'] == boot, 'boot mismatch')
    check(sha(data) == result['sha256'] == expected, 'readback identity')
    check(all(status.get(k) == '0' for k in ('status', 'residual', 'guard_changes')),
          'readback completion/guard')
    check(result['card_after']['bdf'] == '0000:37:09.1' and
          result['card_after']['driver'] == 'myrsread' and
          result['old_after']['bdf'] == '0000:37:04.1' and
          result['old_after']['driver'] is None, 'card identities')
    return request['boot_id']

def snapshot(before, owner, page, after_owner, mode):
    check(len(before) == len(owner) == len(page) == len(after_owner) == 4096,
          'capture lengths')
    check(before == b'\xff' * 4096, 'saved loader page preimage')
    check(page[:FIRST] == before[:FIRST] and page[LAST:] == before[LAST:],
          'loader page outside bounded record')
    check(owner[0x2a0:0xaa0] == after_owner[0x2a0:0xaa0], '512 owner records')
    words = struct.unpack_from('<8I', page, FIRST)
    if mode == 'stop':
        check(words == (MAGIC, NONCE, EPOCH, STOP, READY, ACK, NONCE, EPOCH),
              'STOP record/ACK')
    else:
        check(words == (MAGIC, NONCE, EPOCH, 0, TIME, 0xa5a5a5a5,
                        0xa5a5a5a5, 0xa5a5a5a5), 'deadline record')

def pending_page(before, page, command):
    check(len(page) == 4096 and page[:FIRST] == before[:FIRST] and
          page[LAST:] == before[LAST:], 'pending page bounds')
    check(struct.unpack_from('<8I', page, FIRST) ==
          (MAGIC, NONCE, EPOCH, command, READY, 0xa5a5a5a5,
           0xa5a5a5a5, 0xa5a5a5a5), 'pending READY/no ACK')

def verify(root):
    live = root / 'live'
    check(sha((root / 'candidate.bin').read_bytes()) == IMAGE_SHA, 'candidate SHA')
    check(sha((root / 'build/stop_command.ko').read_bytes()) == MODULE_SHA,
          'command module SHA')
    old_boot = readback(live / 'preflash-read', PREVIOUS_SHA)
    check(readback(live / 'staged-readback', IMAGE_SHA, old_boot) == old_boot,
          'staged boot')
    stage = json.loads((live / 'stage/request.json').read_text())
    staged = json.loads((live / 'stage/result.json').read_text())
    stage_status = fields(live / 'stage/status.txt')
    check(stage['boot_id'] == old_boot and stage['image_sha256'] == IMAGE_SHA and
          staged['stage_completed'] and staged['flash_command_issued'] is False and
          all(stage_status.get(k) == '0' for k in ('status', 'residual', 'guard_changes')),
          'staging proof')
    flash = json.loads((live / 'flash/result.json').read_text())
    flash_preflight = json.loads((live / 'flash/preflight.json').read_text())
    flash_status = fields(live / 'flash/status.txt')
    check(flash['command_completed'] and
          flash_preflight['boot_id'] == old_boot and
          flash_preflight['image_sha256'] == IMAGE_SHA and
          flash_status['status'] == flash_status['residual'] == '0',
          'flash result')
    boot = readback(live / 'persistent-0', IMAGE_SHA)
    check(boot != old_boot, 'reboot not observed')
    readback(live / 'persistent-1', IMAGE_SHA, boot)
    readback(live / 'postcall-flash', IMAGE_SHA, boot)
    run = live / 'stop-run'
    result = json.loads((run / 'result.json').read_text())
    preflight = json.loads((run / 'preflight.json').read_text())
    check(result['boot_id'] == boot and result['page_restored'] and
          result['owner_records_unchanged'] and len(result['runs']) == 2,
          'run result')
    check(preflight['boot_id'] == boot and
          preflight['image_sha256'] == IMAGE_SHA and
          preflight['module_sha256'] == MODULE_SHA,
          'run preflight')
    before = (run / 'page-before.bin').read_bytes()
    owner = (run / 'owner-before.bin').read_bytes()
    for i, mode in enumerate(('stop', 'deadline')):
        pending_page(before, (run / f'run-{i}-ready-page.bin').read_bytes(), 0)
        ready_status = fields(run / f'run-{i}-ready-status.txt')
        check(ready_status['started'] == '1' and ready_status['done'] == '0',
              'READY command was not pending')
        page = (run / f'run-{i}-page.bin').read_bytes()
        own = (run / f'run-{i}-owner.bin').read_bytes()
        snapshot(before, owner, page, own, mode)
        status = fields(run / f'run-{i}-status.txt')
        check(status['done'] == '1' and status['released'] == '0' and
              status['residual'] == '0' and
              status['status'] == ('0' if mode == 'stop' else '2'),
              'command status')
        check(result['runs'][i]['mode'] == mode and
              result['runs'][i]['owner_records_unchanged'], 'run metadata')
        check(status['mailbox'][44:48] == '010b' and
              status['mailbox'][48:64] == '49393630b1101616',
              'wrong one-shot mailbox')
    pending_page(before, (run / 'run-0-stale-page.bin').read_bytes(), 0xdeadbeef)
    check(result['runs'][0]['stale_pending'] is True, 'stale STOP was not rejected')
    return dict(preflash_boot=old_boot, persistent_boot=boot,
                full_flash_reads=4, postcall_full_flash_reads=1,
                stop_calls=2, page_restored=True, owner_records_unchanged=True)

def tamper(root):
    run = root / 'live/stop-run'
    original = [(run / 'page-before.bin').read_bytes(),
                (run / 'owner-before.bin').read_bytes(),
                (run / 'run-0-page.bin').read_bytes(),
                (run / 'run-0-owner.bin').read_bytes()]
    for label, target, index in [('ack', 2, 0x974), ('outside', 2, FIRST - 1),
                                 ('owner', 3, 0x2a0)]:
        parts = original.copy()
        damaged = bytearray(parts[target]); damaged[index] ^= 1
        parts[target] = bytes(damaged)
        try: snapshot(*parts, 'stop')
        except ValueError: continue
        raise AssertionError(f'{label} tamper accepted')

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('--tamper-test', action='store_true')
    a = p.parse_args()
    print(json.dumps(verify(a.root), indent=2))
    if a.tamper_test:
        tamper(a.root)
        print('three tamper cases rejected')
