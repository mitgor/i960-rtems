#!/usr/bin/env python3
"""Replay exact flash, owner and loader-page captures; reject local mutations."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from run_inventory import ADDRESSES, FIRST, LAST, IMAGE_SHA, NONCE, decode, fields

PREVIOUS_SHA = '68451b38b96609fa3a95eb9497fe85a34ac92fec45b912c53612969b1209a988'

def check(ok, message):
    if not ok: raise ValueError(message)

def snapshot(before, owner, page, current_owner):
    check(len(before) == len(owner) == len(page) == len(current_owner) == 4096, 'capture lengths')
    check(before == b'\xff' * 4096, 'loader page preimage')
    check(page[:FIRST] == before[:FIRST] and page[LAST:] == before[LAST:], 'loader page bounds')
    check(owner[0x2a0:0xaa0] == current_owner[0x2a0:0xaa0], '512 owner records')
    result = decode(page)
    check(result['live_prcb_matches_stock_ibr'], 'PRCB pointer')
    other = [i for i, (x, y) in enumerate(zip(owner, current_owner))
             if x != y and not 0x2a0 <= i < 0xaa0]
    check(other == [0xaa0, 0xaa1], 'unclassified dynamic owner-page field')
    return result

def readback(directory, expected, boot=None):
    request = json.loads((directory / 'request.json').read_text())
    result = json.loads((directory / 'result.json').read_text())
    status = fields(directory / 'status.txt')
    data = (directory / 'data.bin').read_bytes()
    check(request['selector'] == 9 and request['length'] == 1048576, 'readback request')
    check(boot is None or request['boot_id'] == boot, 'readback boot')
    check(len(data) == 1048576 and hashlib.sha256(data).hexdigest() == expected and
          result['sha256'] == expected, 'full readback hash')
    check(all(status.get(k) == '0' for k in ('status', 'residual', 'guard_changes')), 'readback status')
    check(result['card_after']['bdf'] == '0000:37:09.1' and
          result['card_after']['driver'] == 'myrsread' and
          result['old_after']['bdf'] == '0000:37:04.1' and
          result['old_after']['driver'] is None, 'card identity')
    return request['boot_id']

def verify(root):
    live = root / 'live'
    check(hashlib.sha256((root / 'candidate.bin').read_bytes()).hexdigest() == IMAGE_SHA,
          'candidate image')
    old_boot = readback(live / 'preflash-read', PREVIOUS_SHA)
    staged_boot = readback(live / 'staged-readback', IMAGE_SHA, old_boot)
    stage = json.loads((live / 'stage/request.json').read_text())
    stage_result = json.loads((live / 'stage/result.json').read_text())
    stage_status = fields(live / 'stage/status.txt')
    check(stage['boot_id'] == old_boot == staged_boot and
          stage['image_sha256'] == IMAGE_SHA and stage_result['stage_completed'] and
          stage_result['flash_command_issued'] is False and
          all(stage_status.get(k) == '0' for k in ('status', 'residual', 'guard_changes')),
          'staging proof')
    flash = json.loads((live / 'flash/result.json').read_text())
    flash_status = fields(live / 'flash/status.txt')
    check(flash['command_completed'] and flash_status['status'] == '0' and
          flash_status['residual'] == '0', 'flash result')
    boot = readback(live / 'persistent-0', IMAGE_SHA)
    check(boot != old_boot, 'reboot not observed')
    for name in ('persistent-1', 'postcall-flash'):
        readback(live / name, IMAGE_SHA, boot)
    first = live / 'inventory-run'
    first_report = snapshot((first / 'page-before.bin').read_bytes(),
                            (first / 'owner-before.bin').read_bytes(),
                            (first / 'run-0-page.bin').read_bytes(),
                            (first / 'run-0-owner.bin').read_bytes())
    check(fields(first / 'run-0-status.txt')['status'] == '0', 'first command status')
    recovered = json.loads((first / 'run-0-recovery.json').read_text())
    check(recovered['report'] == first_report and recovered['loader_page_restored'] and
          recovered['module_released'] and recovered['owner_record_unchanged'],
          'first command recovery')
    repeat = live / 'inventory-repeat'
    result = json.loads((repeat / 'result.json').read_text())
    check(result['boot_id'] == boot and result['owner_records_unchanged'] and
          result['page_restored'] and len(result['runs']) == 2, 'repeat result')
    for ordinal in range(2):
        report = snapshot((repeat / 'page-before.bin').read_bytes(),
                          (repeat / 'owner-before.bin').read_bytes(),
                          (repeat / f'run-{ordinal}-page.bin').read_bytes(),
                          (repeat / f'run-{ordinal}-owner.bin').read_bytes())
        check(fields(repeat / f'run-{ordinal}-status.txt')['status'] == '0',
              'repeat command status')
        check(report['registers'] == result['runs'][ordinal]['registers'] and
              report['stock_prcb_words'] == result['runs'][ordinal]['stock_prcb_words'],
              'repeat decoded report')
    return {'old_boot': old_boot, 'new_boot': boot, 'inventory_calls': 3,
            'full_flash_reads': 5, 'owner_records_unchanged': True,
            'loader_page_restored': True}

def tamper(root):
    d = root / 'live/inventory-repeat'
    before = (d / 'page-before.bin').read_bytes()
    owner = (d / 'owner-before.bin').read_bytes()
    page = (d / 'run-0-page.bin').read_bytes()
    current_owner = (d / 'run-0-owner.bin').read_bytes()
    for label, target, index in [('report', 2, FIRST), ('outside', 2, FIRST - 1),
                                 ('owner', 3, 0x2a0), ('dynamic', 3, 0xaa2)]:
        values = [before, owner, page, current_owner]
        changed = bytearray(values[target]); changed[index] ^= 1
        values[target] = bytes(changed)
        try: snapshot(*values)
        except (ValueError, RuntimeError): continue
        raise AssertionError(f'{label} mutation was accepted')

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('--tamper-test', action='store_true')
    a = p.parse_args()
    print(json.dumps(verify(a.root), indent=2))
    if a.tamper_test:
        tamper(a.root)
        print('four tamper cases rejected')
