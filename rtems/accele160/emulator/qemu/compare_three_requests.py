#!/usr/bin/env python3
"""Check the first ROM mailbox under stock, old-native, and new-native images.

This compares a bounded QEMU prefix and i960 checkpoints. It cannot establish
physical boot behavior or controller command completion.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re


NAMES = ('stock', 'old_native', 'new_native')
ROM_FIELDS = ('option_rom_sha256', 'pci_identity', 'pci_revision',
              'first_config_accesses', 'first_bar_accesses',
              'mailbox_bytes_hex', 'mailbox_requests', 'mailbox_submissions')


def read_case(rom_path: Path, trace_path: Path):
    rom = json.loads(rom_path.read_text())
    trace = trace_path.read_text(errors='replace')
    steps = re.findall(r'^checkpoint bridge-step (.+)$', trace, re.MULTILINE)
    mailboxes = re.findall(r'^checkpoint mailbox-bytes ([0-9a-f]{128})$',
                           trace, re.MULTILINE)
    reports = re.findall(r'^checkpoint native-report (.+)$', trace,
                         re.MULTILINE)
    if len(steps) != 2 or len(mailboxes) != 1:
        raise ValueError(f'{trace_path}: expected two steps and one request')
    if bytes.fromhex(mailboxes[0]) != bytes.fromhex(rom['mailbox_bytes_hex'][0]):
        raise ValueError(f'{trace_path}: QEMU and i960 mailbox bytes differ')
    return rom, trace, steps, reports


def compare(cases):
    stock = cases['stock'][0]
    if any(not stock[field] for field in ROM_FIELDS):
        raise ValueError('stock capture is missing a required ROM stream')
    for name in NAMES[1:]:
        rom = cases[name][0]
        for field in ROM_FIELDS:
            if rom[field] != stock[field]:
                raise ValueError(f'{name}: first difference in {field}')
    packet = bytes.fromhex(stock['mailbox_bytes_hex'][0])
    expected = {'id': 127, 'opcode': 32, 'control': 16,
                'transfer_bytes': 512, 'ioctl': 1,
                'sg0_dma': 0x9f3e0, 'sg0_bytes': 512}
    if len(packet) != 64 or stock['mailbox_requests'] != [expected]:
        raise ValueError('not the observed GET_CTLR_INFO transaction')
    if any(cases[name][0]['stock_ctlr_info_completed'] for name in NAMES):
        raise ValueError('this bounded comparison unexpectedly completed')
    if not all(cases[name][0]['bar_trace_limited'] for name in NAMES):
        raise ValueError('update the trace-limit claim for this run')
    if 'next-stage=1' not in cases['stock'][2][0]:
        raise ValueError('stock did not reach its next startup stage')
    for name in NAMES[1:]:
        steps, reports = cases[name][2:]
        if (not reports or 'ip=c0010030' not in steps[0] or
                'next-stage=0' not in steps[0] or
                '50415353' not in reports[0]):
            raise ValueError(f'{name}: RTEMS PASS/park milestone absent')
    result = {
        'result': 'MATCHED_REQUEST_DIFFERENT_CONTROLLER_PROGRESS',
        'scope': 'five-second bounded QEMU ROM plus exploratory i960 replay',
        'images': {name: cases[name][0]['image_sha256'] for name in NAMES},
        'first_request': {
            'mailbox_sha256': hashlib.sha256(packet).hexdigest(),
            'mailbox_hex': packet.hex(),
            **expected,
        },
        'identical_fields': list(ROM_FIELDS),
        'rom_block_counts': {name: cases[name][0]['rom_block_count']
                             for name in NAMES},
        'rom_block_digests': {name: cases[name][0]['rom_blocks_sha256']
                              for name in NAMES},
        'controller_progress': {
            'stock': 'next startup stage',
            'old_native': 'RTEMS PASS then park',
            'new_native': 'RTEMS PASS/HST0 then park',
        },
        'completion_observed': False,
        'bar_trace_limited': True,
        'model_limits': [
            'reset selector 11 is exploratory',
            'QEMU SeaBIOS is not the HP Z400 BIOS',
            'stock and native images do not complete this request in this bounded replay',
        ],
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in NAMES:
        parser.add_argument(f'--{name.replace("_", "-")}-rom', type=Path,
                            required=True)
        parser.add_argument(f'--{name.replace("_", "-")}-trace', type=Path,
                            required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    cases = {name: read_case(getattr(args, f'{name}_rom'),
                             getattr(args, f'{name}_trace')) for name in NAMES}
    result = compare(cases)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(result['result'])


if __name__ == '__main__':
    main()
