#!/usr/bin/env python3
"""Check the bounded stock/native ring-slot 3 and slot 4 offline evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def one(pattern, text, label):
    matches = re.findall(pattern, text)
    if len(matches) != 1:
        raise AssertionError(f'{label}: expected one match, found {len(matches)}')
    return matches[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('observer-run', 'repeat-run', 'stock-positive-run',
                 'stock-negative-run', 'stock-scsi-receipt', 'emulator',
                 'qemu', 'observer-image', 'repeat-image', 'output'):
        ap.add_argument('--' + name, required=True, type=Path)
    args = ap.parse_args()
    observer = (args.observer_run / 'qemu.log').read_text()
    repeat = (args.repeat_run / 'qemu.log').read_text()
    stock_positive = (args.stock_positive_run / 'qemu.log').read_text()
    stock_negative = (args.stock_negative_run / 'qemu.log').read_text()
    observer_serial = (args.observer_run / 'serial.log').read_text()
    repeat_serial = (args.repeat_run / 'serial.log').read_text()
    stock_receipt = json.loads(args.stock_scsi_receipt.read_text())
    if stock_receipt.get('gate') != 'PASS':
        raise AssertionError('stock SCSI/ISP boundary receipt failed')
    model = re.compile(
        r'native next event=([34]) .*?state=0x([0-9a-f]{8}) '
        r'id=(\d+) opcode=0x([0-9a-f]{2}) '
        r'output=0x([0-9a-f]{8}) length=(\d+) '
        r'status-cursor=0x([0-9a-f]{8}) completions=(\d+) '
        r'outbound=0x([0-9a-f]{8}) no-guest-copy=1')
    old = {int(m[0]): m for m in model.findall(observer)}
    new = {int(m[0]): m for m in model.findall(repeat)}
    if set(old) != {3, 4} or set(new) != {3, 4}:
        raise AssertionError('both native images must observe slots 3 and 4')
    if old[3][1:4] != ('00000002', '1', '01') or old[3][5] != '1004' or (
        old[3][7], old[3][8]) != ('3', '00000000'):
        raise AssertionError('observer slot 3 was not read-only')
    if new[3][1:4] != ('00000002', '1', '01') or new[3][5] != '1004' or (
        new[3][7], new[3][8]) != ('4', '00000002'):
        raise AssertionError('repeat image did not complete slot 3')
    for label, row, count in (('observer', old[4], '3'), ('repeat', new[4], '4')):
        if row[1] != '00000002' or row[3] != '02' or row[5] != '36' or (
            row[7], row[8]) != (count, '00000000'):
            raise AssertionError(f'{label}: slot 4 did not remain read-only')
        if not 0 < int(row[2]) <= 0xffff:
            raise AssertionError(f'{label}: invalid dynamic slot 4 ID')
    if old[3][4] == new[3][4]:
        raise AssertionError('dynamic slot 3 output address did not vary')
    if 'native next guest-mirror rejected event=3' not in observer or (
        'native next mirrored event=3' in observer):
        raise AssertionError('old-image negative control did not reject')
    expected_sha = 'a3f72f98e18667d7c80eebac996b77f465bce5d5024a8b3ec3c70d2a285572f8'
    mirrored = one(
        r'native next mirrored event=3 output=0x([0-9a-f]{8}) '
        r'bytes=1004 sha256=([0-9a-f]{64}) '
        r'status=(01000000ecffffff) slot-word0=0 '
        r'outbound=0x02 irq=1', repeat, 'native slot 3 mirror')
    if mirrored[1] != expected_sha or (
        'native next guest-mirror accepted event=3' not in repeat):
        raise AssertionError('native slot 3 mirror did not match stock bytes')
    if 'native next mirrored event=4' in repeat or (
        '__MYRS_PROBE_END__' in repeat_serial) or (
        '__MYRS_PROBE_END__' in observer_serial):
        raise AssertionError('unmodeled slot 4 acquired a completion')
    if 'lp reset requested; unmodeled' not in repeat:
        raise AssertionError('expected Linux error-recovery/reset boundary absent')
    if 'stock next guest-mirror accepted event=3' not in stock_positive:
        raise AssertionError('stock positive control did not mirror slot 3')
    if 'stock next mutated guest prefill byte=0x' not in stock_negative or (
        'stock next guest-mirror rejected event=3' not in stock_negative) or (
        'stock next mirrored event=3' in stock_negative):
        raise AssertionError('mutated guest prefill was not rejected')
    receipt = {
        'gate': 'PASS',
        'observer_image_sha256': sha(args.observer_image),
        'repeat_image_sha256': sha(args.repeat_image),
        'emulator_sha256': sha(args.emulator),
        'qemu_sha256': sha(args.qemu),
        'stock_positive_slot3_mirror': True,
        'stock_mutated_prefill_rejected': True,
        'observer_slot3_rejected': True,
        'native_repeat_slot3_output_sha256': mirrored[1],
        'native_repeat_slot3_status_hex': mirrored[2],
        'native_slot4_observed': True,
        'native_slot4_completed': False,
        'linux_probe_completed': False,
        'physical_card_tested': False,
        'safe_to_flash': False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + '\n')
    print('next_ring_pair=PASS slot3_mirrored=True slot4_pending=True')


if __name__ == '__main__':
    main()
