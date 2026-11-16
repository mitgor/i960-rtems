#!/usr/bin/env python3
"""Pin two stock first-ring follow-up completions across guest DMA layouts."""
import argparse
import hashlib
import json
from pathlib import Path
import re

HEALTH_SHA = '67dc9bba5de17ef407a77f5e3382a7d89fcc4e7f7b4f287d7e682baece59ff32'
PDEV_SHA = '9e17de7358c0c4cb07a8a7a511c00157a17a38656412e778b69a80ca6b501a41'
MODEL = re.compile(r'stock followup model event=(\d) slot1=0x([0-9a-f]{8}) '
                   r'slot2=0x([0-9a-f]{8}) status1=([0-9a-f]{16}) '
                   r'status2=([0-9a-f]{16}) health-sha256=([0-9a-f]{64}) '
                   r'pdev-sha256=(none|[0-9a-f]{64}).*?ring-cursor=0x([0-9a-f]{8}) '
                   r'queue-head=0x([0-9a-f]{8}).*?descriptor=([0-9a-f,]{53}) '
                   r'outbound=0x([0-9a-f]{8})')
SLOT = re.compile(r'ring followup event=([12]) slot=([12]) '
                  r'dma=0x([0-9a-f]{8}) hex=([0-9a-f]{128})')


def inspect(path):
    qemu = (path / 'qemu.log').read_text(errors='replace')
    emu = (path / 'emu.log').read_text(errors='replace')
    if 'stock ring mirrored output=' not in qemu or 'health-dma1-gate=1' not in qemu:
        raise AssertionError(f'{path}: first-ring mirror or health gate missing')
    slots = {(int(e), int(i)): (int(a, 16), bytes.fromhex(raw))
             for e, i, a, raw in SLOT.findall(qemu)}
    models = MODEL.findall(qemu)
    if len(models) != 2 or (1, 1) not in slots or (2, 2) not in slots:
        raise AssertionError(f'{path}: missing follow-up slot/model')
    first = slots[(1, 1)][1]
    second = slots[(2, 2)][1]
    health_dma = int.from_bytes(first[32:40], 'little')
    pdev_dma = int.from_bytes(second[32:40], 'little')
    if (first[0:4] != bytes.fromhex('02002050') or first[21] != 0x11 or
            first[40:44] != bytes.fromhex('80000000') or
            second[0:4] != bytes.fromhex('01002050') or second[21] != 0x05 or
            second[40:44] != bytes.fromhex('00020000')):
        raise AssertionError(f'{path}: wrong slot shapes')
    expected = ((1, '00000000', '00000000', '0000000200000000',
                 '0000000000000000', HEALTH_SHA, 'none', '06340080',
                 f'00000000,{health_dma:08x},00000000,c060c300,00000080,0000003f'),
                (2, '00000000', '00000000', '0000000200000000',
                 '0000000100000000', HEALTH_SHA, PDEV_SHA, '063400c0',
                 f'00000000,{pdev_dma:08x},00000000,c060c300,00000200,0000003f'))
    for fields, want in zip(models, expected):
        event, slot1, slot2, status1, status2, health, pdev, cursor, queue, descriptor, outbound = fields
        if (int(event), slot1, slot2, status1, status2, health, pdev,
                cursor, descriptor) != want or queue != '00000000' or outbound != '00000002':
            raise AssertionError(f'{path}: stock completion mismatch: {fields}')
    for kind, address, length in (('health', health_dma, 128),
                                  ('pdev', pdev_dma, 512)):
        pattern = (rf'checkpoint mu-dma1-ring-{kind} descriptor=c0611320 '
                   rf'local=c060c300 host={address:08x} bytes={length} eoc=1')
        if not re.search(pattern, emu):
            raise AssertionError(f'{path}: missing actual DMA1 {kind} EOC')
    if 'stock followup pdev window rejected' in qemu or 'model staging rejected' in qemu:
        raise AssertionError(f'{path}: staging rejected')
    return {'health_dma': f'0x{health_dma:08x}',
            'pdev_dma': f'0x{pdev_dma:08x}',
            'health_sha256': HEALTH_SHA, 'pdev_sha256': PDEV_SHA,
            'health_status_hex': '0200000000000000',
            'pdev_status_hex': '0100000000000000',
            'guest_followup_mirror': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--first-run', type=Path, required=True)
    parser.add_argument('--repeat-run', type=Path, required=True)
    parser.add_argument('--health-fixture', type=Path, required=True)
    parser.add_argument('--pdev-fixture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if hashlib.sha256(args.health_fixture.read_bytes()).hexdigest() != HEALTH_SHA:
        raise AssertionError('health fixture hash mismatch')
    if hashlib.sha256(args.pdev_fixture.read_bytes()).hexdigest() != PDEV_SHA:
        raise AssertionError('pdev fixture hash mismatch')
    first, repeat = inspect(args.first_run), inspect(args.repeat_run)
    if first['health_dma'] == repeat['health_dma'] or first['pdev_dma'] == repeat['pdev_dma']:
        raise AssertionError('dynamic DMA layouts did not differ')
    receipt = {'gate': 'PASS', 'first': first, 'repeat': repeat,
               'scope': 'stock model IOCTL11 and IOCTL05 DMA1/status/ODB; guest follow-up copy disabled',
               'physical_card_tested': False, 'safe_to_flash': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + '\n')
    print('stock_followup_dma1=PASS dynamic_layouts=2 guest_mirror=False')


if __name__ == '__main__':
    main()
