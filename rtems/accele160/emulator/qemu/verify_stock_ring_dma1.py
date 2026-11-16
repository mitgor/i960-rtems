#!/usr/bin/env python3
"""Verify bounded stock first-ring DMA1 continuation without guest mirroring."""
import argparse
import hashlib
import json
from pathlib import Path
import re


SNAP = re.compile(r'accele160 EXPLORE ring model phase=([^ ]+) slot-word0=0x([0-9a-f]{8}) status=([0-9a-f]{16}) output-sha256=([0-9a-f]{64})')
GUEST = re.compile(r'accele160 EXPLORE ring guest phase=([^ ]+) status=([0-9a-f]{16}) health-first=([0-9a-f]{16}) output-sha256=([0-9a-f]{64})')
DESC = re.compile(r'accele160 EXPLORE stock dma1-first status=0x([0-9a-f]{8}) control=0x([0-9a-f]{8}) descriptor-pointer=0x([0-9a-f]{8}) descriptor=([0-9a-f]{8}),([0-9a-f]{8}),([0-9a-f]{8}),([0-9a-f]{8}),([0-9a-f]{8}),([0-9a-f]{8})')
SLOT = re.compile(r'accele160 EXPLORE memory-mailbox slot dma=0x([0-9a-f]{16}) hex=([0-9a-f]{128})')


def inspect(path, image, complete):
    rom = json.loads((path / 'rom.json').read_text())
    qemu = (path / 'qemu.log').read_text(errors='replace')
    emu = (path / 'emu.log').read_text(errors='replace')
    if rom['image_sha256'] != hashlib.sha256(image.read_bytes()).hexdigest():
        raise AssertionError(f'{path}: image mismatch')
    if [x['ioctl'] for x in rom['mailbox_requests'][:6]] != [1, 0x11, 0x15, 0xd0, 0x2d, 0x8e]:
        raise AssertionError(f'{path}: request sequence mismatch')
    snapshots, guests, descriptors, slots = (SNAP.findall(qemu), GUEST.findall(qemu),
                                             DESC.findall(qemu), SLOT.findall(qemu))
    if len(snapshots) != 2 or len(guests) != 2 or len(descriptors) != 1 or len(slots) != 1:
        raise AssertionError(f'{path}: missing bounded trace')
    first, last = snapshots
    if first[0] != 'before-idb10' or first[1] != '50200001' or first[2] != '0000000000000000':
        raise AssertionError(f'{path}: bad first slot/status')
    if last[1] != '00000000' or guests[0][1:] != guests[1][1:]:
        raise AssertionError(f'{path}: slot not consumed or guest changed')
    descriptor = [int(word, 16) for word in descriptors[0]]
    slot = bytes.fromhex(slots[0][1])
    output_bus = int.from_bytes(slot[32:40], 'little')
    if (descriptor[2:] != [0xc0611320, 0, output_bus, 0, 0xc060c300, 1004, 0x3f] or
            int(descriptors[0][0], 16) != 0):
        raise AssertionError(f'{path}: DMA1 descriptor differs from observed shape')
    output_hex = re.findall(r'accele160 EXPLORE ring model output-hex=([0-9a-f]{2008})', qemu)
    if len(output_hex) != 1 or hashlib.sha256(bytes.fromhex(output_hex[0])).hexdigest() != last[3]:
        raise AssertionError(f'{path}: output bytes/hash mismatch')
    copy = 'checkpoint mu-dma1-ring-output' in emu
    if copy != complete:
        raise AssertionError(f'{path}: DMA1 EOC path mismatch')
    if complete:
        if last[2] != '00000001ffffffec':
            raise AssertionError(f'{path}: wrong status words')
    elif last[2] != '0000000000000000' or last[3] != first[3]:
        raise AssertionError(f'{path}: negative run unexpectedly completed')
    return {'image_sha256': rom['image_sha256'],
            'output_bus': f'0x{output_bus:08x}',
            'descriptor': [f'0x{v:08x}' for v in descriptor[2:]],
            'dma1_copy_observed': copy,
            'status_words': last[2], 'output_sha256': last[3],
            'guest_unchanged': True,
            'output': bytes.fromhex(output_hex[0])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('negative-run', 'positive-run', 'stock-image', 'legacy-reply', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--repeat-run', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    negative = inspect(args.negative_run, args.stock_image, False)
    positive = inspect(args.positive_run, args.stock_image, True)
    output = positive.pop('output')
    negative.pop('output')
    repeat = None
    if args.repeat_run:
        repeat = inspect(args.repeat_run, args.stock_image, True)
        repeated_output = repeat.pop('output')
        repeated_qemu = (args.repeat_run / 'qemu.log').read_text(errors='replace')
        if (repeated_output != output or
                repeat['status_words'] != positive['status_words'] or
                'accele160 EXPLORE stock ring outbound=0x00000002 no-guest-mirror=1'
                not in repeated_qemu):
            raise AssertionError('repeat output/status/ODB2 mismatch')
        if ((args.repeat_run / 'model-first-output-1004.bin').read_bytes() != output or
                (args.repeat_run / 'model-first-status-8.bin').read_bytes() !=
                bytes.fromhex('01000000ecffffff')):
            raise AssertionError('repeat saved raw fixture mismatch')
        repeat['outbound_odb2_observed'] = True
    legacy = args.legacy_reply.read_bytes()
    if len(output) != 1004 or len(legacy) != 512 or output[:512] != legacy or any(output[512:]):
        raise AssertionError('ring output does not match legacy controller-info plus zero tail')
    raw_output = (args.positive_run / 'model-first-output-1004.bin').read_bytes()
    raw_status = (args.positive_run / 'model-first-status-8.bin').read_bytes()
    if raw_output != output or raw_status != bytes.fromhex('01000000ecffffff'):
        raise AssertionError('saved raw fixture mismatch')
    receipt = {'gate': 'PASS', 'negative': negative, 'positive': positive,
               'status_bytes': raw_status.hex(),
               'status_decoded': {'id': 1, 'status': 0, 'sense_len': 0, 'residual': -20},
               'output_first512_matches_legacy': True,
               'output_tail492_zero': True,
               'repeat': repeat,
               'scope': 'opt-in stock MU DMA1 model continuation; no guest mirroring',
               'physical_card_tested': False, 'safe_to_flash': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + '\n')
    print('stock_ring_dma1=PASS status_id1=True output_legacy512=True guest_unchanged=True')


if __name__ == '__main__':
    main()
