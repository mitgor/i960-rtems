#!/usr/bin/env python3
"""Check paired opt-in native first-ring observation without a ring reply."""
import argparse
import hashlib
import json
from pathlib import Path
import re


SLOT = re.compile(r'accele160 EXPLORE memory-mailbox slot dma=0x([0-9a-f]{16}) hex=([0-9a-f]{128})')
STAGED = re.compile(r'checkpoint memory-mailbox-slot dma=([0-9a-f]{16}) bytes=([0-9a-f]{128}) staged=1 completion=unmodeled')
DOORBELL = re.compile(r'accele160 EXPLORE native ring staged dma=0x([0-9a-f]+) output=0x([0-9a-f]+) local-idb=0x([0-9a-f]+) no-completion=1')
REPORT = re.compile(r'accele160 EXPLORE native ring observer marker=0x([0-9a-f]{8}) state=0x([0-9a-f]{8}) digest=0x([0-9a-f]{8}) cursor=0x([0-9a-f]{8}) output=0x([0-9a-f]{8}) length=([0-9]+) id=([0-9]+) seen-idb=0x([0-9a-f]{8}) completions=([0-9]+)')
MODEL = re.compile(r'accele160 EXPLORE (?:native )?ring model phase=([^ ]+) slot-word0=0x([0-9a-f]{8}) status=([0-9a-f]{16}) output-sha256=([0-9a-f]{64})')
GUEST = re.compile(r'accele160 EXPLORE (?:native )?ring guest phase=([^ ]+) status=([0-9a-f]{16}) health-first=([0-9a-f]{16}) output-sha256=([0-9a-f]{64})')


def fnv1a(data):
    digest = 0x811c9dc5
    for value in data:
        digest = ((digest ^ value) * 0x01000193) & 0xffffffff
    return digest


def one(pattern, text, label):
    found = pattern.findall(text)
    if len(found) != 1:
        raise AssertionError(f'{label}: expected exactly one match, got {len(found)}')
    return found[0]


def inspect(run, image, observed):
    rom = json.loads((run / 'rom.json').read_text())
    qemu = (run / 'qemu.log').read_text(errors='replace')
    emu = (run / 'emu.log').read_text(errors='replace')
    if rom['image_sha256'] != hashlib.sha256(image.read_bytes()).hexdigest():
        raise AssertionError(f'{run}: image hash mismatch')
    if [item['ioctl'] for item in rom['mailbox_requests'][:6]] != [1, 0x11, 0x15, 0xd0, 0x2d, 0x8e]:
        raise AssertionError(f'{run}: incomplete setup sequence')
    if 'native set-mbox completion id=1 status=0x0000' not in qemu:
        raise AssertionError(f'{run}: no native 0x8e completion')
    dma, slot_hex = one(SLOT, qemu, f'{run} guest slot')
    model_dma, model_hex = one(STAGED, emu, f'{run} model slot')
    if (dma, slot_hex) != (model_dma, model_hex):
        raise AssertionError(f'{run}: guest/model slot mismatch')
    slot = bytes.fromhex(slot_hex)
    ring = int.from_bytes(slot[0:4], 'little')
    output = int.from_bytes(slot[32:40], 'little')
    if ring != 0x50200001 or int(dma, 16) < 0x100000 or output < 0x100000:
        raise AssertionError(f'{run}: unexpected first GET_CTLR_INFO slot')
    staged = one(DOORBELL, qemu, f'{run} IDB10')
    if int(staged[0], 16) != int(dma, 16) or int(staged[1], 16) != output or not int(staged[2], 16) & 0x10:
        raise AssertionError(f'{run}: D10 not latched at slot address')
    report = one(REPORT, qemu, f'{run} observer report')
    words = [int(value, 16) if i in (0, 1, 2, 3, 4, 7) else int(value)
             for i, value in enumerate(report)]
    if observed:
        if words != [0x31474e52, 2, fnv1a(slot), int(dma, 16), output, 1004, 1, 0x10, 0]:
            raise AssertionError(f'{run}: native observer report does not match exact guest slot')
    elif any(words):
        raise AssertionError(f'{run}: old image unexpectedly reported ring observation')
    model = MODEL.findall(qemu)
    guest = GUEST.findall(qemu)
    if len(model) != 2 or len(guest) != 2 or model[0][0] != 'before-idb10' or model[1][0] != 'after-5m':
        raise AssertionError(f'{run}: missing before/after snapshots')
    if (model[0][1:] != model[1][1:] or model[0][1] != '50200001' or
            model[0][2] != '0000000000000000' or guest[0][1:] != guest[1][1:] or
            guest[0][1] != '0000000000000000' or
            not any('native ring outbound=0x00000000 ' + suffix in qemu
                    for suffix in ('no-host-status-write=1', 'no-guest-mirror=1'))):
        raise AssertionError(f'{run}: ring or guest memory changed without authorization')
    return {'image_sha256': rom['image_sha256'], 'slot_dma': f'0x{dma}',
            'slot_sha256': hashlib.sha256(slot).hexdigest(),
            'slot_fnv1a': f'0x{fnv1a(slot):08x}',
            'observer_state': words[1], 'seen_idb10': bool(int(staged[2], 16) & 0x10),
            'status_unchanged': True, 'output_unchanged': True,
            'guest_unchanged': True, 'completion_count': words[8]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('old-run', 'observer-run', 'old-image', 'observer-image', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    receipt = {'gate': 'PASS',
               'old': inspect(args.old_run, args.old_image, False),
               'observer': inspect(args.observer_run, args.observer_image, True),
               'scope': 'opt-in QEMU/i960 read-only first-ring observer',
               'physical_card_tested': False, 'safe_to_flash': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + '\n')
    print('native_ring_observer=PASS old_unobserved=True new_observed=True no_reply=True')


if __name__ == '__main__':
    main()
