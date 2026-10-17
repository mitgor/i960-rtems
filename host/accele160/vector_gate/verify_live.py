#!/usr/bin/env python3
"""Replay vector gate captures and reject report/page/owner mutations."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from run_vector import IMAGE_SHA, MODULE_SHA, HANDLER_SHA, FIRST, LAST, decode, fields

PREVIOUS_SHA = 'ef5635d38bf397ff13fa1140ef6265de0b300c70ad8b157c17427013a1d2abb5'

def check(ok, message):
    if not ok: raise ValueError(message)
def sha(data): return hashlib.sha256(data).hexdigest()

def readback(path, expected, boot=None):
    req = json.loads((path / 'request.json').read_text())
    result = json.loads((path / 'result.json').read_text())
    status = fields(path / 'status.txt')
    data = (path / 'data.bin').read_bytes()
    check(req['selector'] == 9 and req['length'] == len(data) == 1048576,
          'full read selector/length')
    check(boot is None or req['boot_id'] == boot, 'read boot ID')
    check(sha(data) == result['sha256'] == expected, 'full read SHA')
    check(all(status.get(k) == '0' for k in ('status', 'residual', 'guard_changes')),
          'read status/guards')
    check(result['card_after']['bdf'] == '0000:37:09.1' and
          result['card_after']['driver'] == 'myrsread' and
          result['old_after']['bdf'] == '0000:37:04.1' and
          result['old_after']['driver'] is None, 'card identities')
    return req['boot_id']

def snapshot(before, owner, page, after_owner, handler):
    check(len(before) == len(owner) == len(page) == len(after_owner) == 4096,
          'capture lengths')
    prefix = handler[0xf000 - 0xe1d8:]
    check(len(handler) == 3868 and sha(handler) == HANDLER_SHA and
          before == prefix + b'\xff' * (4096 - len(prefix)),
          'saved loader page/code prefix')
    check(page[:FIRST] == before[:FIRST] and page[LAST:] == before[LAST:],
          'page outside bounded report')
    check(owner[0x2a0:0xaa0] == after_owner[0x2a0:0xaa0],
          '512 owner/count records')
    return decode(page)

def stop_snapshot(before, owner, page, after_owner, mode):
    check(len(before) == len(owner) == len(page) == len(after_owner) == 4096,
          'STOP capture lengths')
    check(page[:0x960] == before[:0x960] and page[0x980:] == before[0x980:],
          'STOP page outside record')
    check(owner[0x2a0:0xaa0] == after_owner[0x2a0:0xaa0],
          'STOP owner records')
    words = struct.unpack_from('<8I', page, 0x960)
    if mode == 'stop':
        check(words == (0x31504f54, 0x161610b1, 1, 0x504f5453,
                        0x59444152, 0x214b4341, 0x161610b1, 1),
              'STOP ACK')
    else:
        check(words == (0x31504f54, 0x161610b1, 1, 0, 0x454d4954,
                        0xa5a5a5a5, 0xa5a5a5a5, 0xa5a5a5a5),
              'STOP deadline')

def verify(root):
    live = root / 'live'
    check(sha((root / 'candidate.bin').read_bytes()) == IMAGE_SHA,
          'candidate image')
    check(sha((root / 'build/vector_command.ko').read_bytes()) == MODULE_SHA,
          'command module')
    handler = (root / 'build/handler.bin').read_bytes()
    check(len(handler) == 3868 and sha(handler) == HANDLER_SHA, 'handler')
    old_boot = readback(live / 'preflash-read', PREVIOUS_SHA)
    check(readback(live / 'staged-readback', IMAGE_SHA, old_boot) == old_boot,
          'staged boot')
    stage = json.loads((live / 'stage/request.json').read_text())
    stage_result = json.loads((live / 'stage/result.json').read_text())
    stage_status = fields(live / 'stage/status.txt')
    check(stage['boot_id'] == old_boot and stage['image_sha256'] == IMAGE_SHA and
          stage_result['stage_completed'] and
          stage_result['flash_command_issued'] is False and
          all(stage_status.get(k) == '0' for k in ('status', 'residual', 'guard_changes')),
          'staging proof')
    flash = json.loads((live / 'flash/result.json').read_text())
    flash_preflight = json.loads((live / 'flash/preflight.json').read_text())
    flash_status = fields(live / 'flash/status.txt')
    check(flash['command_completed'] and
          flash_preflight['boot_id'] == old_boot and
          flash_preflight['image_sha256'] == IMAGE_SHA and
          flash_status['status'] == flash_status['residual'] == '0',
          'flash proof')
    boot = readback(live / 'persistent-0', IMAGE_SHA)
    check(boot != old_boot, 'new boot missing')
    readback(live / 'persistent-1', IMAGE_SHA, boot)
    readback(live / 'postcall-flash', IMAGE_SHA, boot)
    readback(live / 'postcompat-flash', IMAGE_SHA, boot)
    run = live / 'vector-run'
    preflight = json.loads((run / 'preflight.json').read_text())
    result = json.loads((run / 'result.json').read_text())
    status = fields(run / 'status.txt')
    check(preflight['boot_id'] == result['boot_id'] == boot and
          preflight['image_sha256'] == IMAGE_SHA and
          preflight['module_sha256'] == MODULE_SHA and
          preflight['handler_sha256'] == HANDLER_SHA and
          result['page_restored'] and result['owner_records_unchanged'],
          'run preflight/result')
    check(status['done'] == '1' and status['status'] ==
          status['residual'] == '0' and status['mailbox'][44:48] == '010c' and
          status['mailbox'][48:64] == '49393630c1101616', 'command result')
    report = snapshot((run / 'page-before.bin').read_bytes(),
                      (run / 'owner-before.bin').read_bytes(),
                      (run / 'page-after.bin').read_bytes(),
                      (run / 'owner-after.bin').read_bytes(), handler)
    check(report == result['report'], 'decoded report drift')
    stop = live / 'stop-compat'
    stop_preflight = json.loads((stop / 'preflight.json').read_text())
    stop_result = json.loads((stop / 'result.json').read_text())
    check(stop_preflight['boot_id'] == stop_result['boot_id'] == boot and
          stop_preflight['image_sha256'] == IMAGE_SHA and
          stop_preflight['handler_sha256'] == HANDLER_SHA and
          stop_result['page_restored'] and
          stop_result['owner_records_unchanged'] and
          len(stop_result['runs']) == 2, 'STOP compatibility preflight/result')
    stop_before = (stop / 'page-before.bin').read_bytes()
    prefix = handler[0xf000 - 0xe1d8:]
    check(stop_before == prefix + b'\xff' * (4096 - len(prefix)),
          'STOP saved page/code tail')
    stop_owner = (stop / 'owner-before.bin').read_bytes()
    for i, mode in enumerate(('stop', 'deadline')):
        stop_snapshot(stop_before, stop_owner,
                      (stop / f'run-{i}-page.bin').read_bytes(),
                      (stop / f'run-{i}-owner.bin').read_bytes(), mode)
        state = fields(stop / f'run-{i}-status.txt')
        check(state['done'] == '1' and state['status'] ==
              ('0' if mode == 'stop' else '2') and state['residual'] == '0',
              'STOP compatibility command status')
    check(stop_result['runs'][0]['stale_pending'] is True,
          'stale STOP compatibility')
    return dict(preflash_boot=old_boot, persistent_boot=boot,
                full_flash_reads=6, vector_calls=1, stop_compat_calls=2,
                report=report, page_restored=True,
                owner_records_unchanged=True)

def tamper(root):
    run = root / 'live/vector-run'
    parts = [(run / n).read_bytes() for n in
             ('page-before.bin', 'owner-before.bin',
              'page-after.bin', 'owner-after.bin')]
    handler = (root / 'build/handler.bin').read_bytes()
    for label, target, index in [('vector', 2, FIRST + 12),
                                 ('outside', 2, FIRST - 1),
                                 ('owner', 3, 0x2a0)]:
        changed = parts.copy()
        data = bytearray(changed[target]); data[index] ^= 1
        changed[target] = bytes(data)
        try: snapshot(*changed, handler)
        except (ValueError, RuntimeError): continue
        raise AssertionError(f'{label} mutation accepted')

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('--tamper-test', action='store_true')
    a = p.parse_args()
    print(json.dumps(verify(a.root), indent=2))
    if a.tamper_test:
        tamper(a.root)
        print('three tamper cases rejected')
