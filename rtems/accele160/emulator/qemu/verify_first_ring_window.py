#!/usr/bin/env python3
"""Check bounded stock/native first memory-ring observations; never infer a reply."""
import argparse
import hashlib
import json
from pathlib import Path
import re

PATTERN = re.compile(r'accele160 EXPLORE (?:native )?ring model phase=([^ ]+) '
                     r'slot-word0=0x([0-9a-f]{8}) status=([0-9a-f]{16}) '
                     r'output-sha256=([0-9a-f]{64})')
GUEST = re.compile(r'accele160 EXPLORE (?:native )?ring guest phase=([^ ]+) '
                   r'status=([0-9a-f]{16}) .*output-sha256=([0-9a-f]{64})')


def observe(path, image, stock):
    rom = json.loads((path / 'rom.json').read_text())
    qemu = (path / 'qemu.log').read_text(errors='replace')
    emu = (path / 'emu.log').read_text(errors='replace')
    model = PATTERN.findall(qemu)
    guest = GUEST.findall(qemu)
    if len(model) != 2 or len(guest) != 2:
        raise AssertionError(f'{path}: missing before/after snapshots')
    if ([x['ioctl'] for x in rom['mailbox_requests'][:6]] !=
            [1, 0x11, 0x15, 0xd0, 0x2d, 0x8e]):
        raise AssertionError(f'{path}: wrong mailbox sequence')
    if rom['image_sha256'] != hashlib.sha256(image.read_bytes()).hexdigest():
        raise AssertionError(f'{path}: image hash mismatch')
    first, last = model
    if (first[0] != 'before-idb10' or first[1] != '50200001' or
            first[2] != '0000000000000000'):
        raise AssertionError(f'{path}: wrong staged command/status')
    if (last[1] != ('00000000' if stock else '50200001') or
            last[2] != '0000000000000000' or last[3] != first[3]):
        raise AssertionError(f'{path}: unexpected model status or output')
    if guest[0][1:] != guest[1][1:] or guest[0][2] != first[3]:
        raise AssertionError(f'{path}: guest memory changed without mirrored completion')
    if stock:
        if ('mmbox-ring-scan=1' not in emu or
                'stock set-mbox completion reflected' not in qemu):
            raise AssertionError(f'{path}: stock scanner path missing')
    else:
        if ('native set-mbox completion id=1 status=0x0000' not in qemu or
                not any('native ring outbound=0x00000000 ' + suffix in qemu
                        for suffix in ('no-host-status-write=1', 'no-guest-mirror=1'))):
            raise AssertionError(f'{path}: native pending path missing')
    return {'image_sha256': rom['image_sha256'],
            'slot_before': first[1], 'slot_after': last[1],
            'model_status_after': last[2],
            'output_sha256_before_and_after': first[3],
            'guest_status_unchanged': True, 'ring_reply_observed': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-run', type=Path, required=True)
    p.add_argument('--native-run', type=Path, required=True)
    p.add_argument('--stock-image', type=Path, required=True)
    p.add_argument('--native-image', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    receipt = {
        'gate': 'PASS',
        'stock': observe(args.stock_run, args.stock_image, True),
        'native': observe(args.native_run, args.native_image, False),
        'scope': 'bounded exploratory first-slot observation; no ring reply',
        'physical_card_tested': False, 'safe_to_flash': False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + '\n')
    print('first_ring_window=PASS stock_consumed=True native_pending=True')


if __name__ == '__main__':
    main()
