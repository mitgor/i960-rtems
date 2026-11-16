#!/usr/bin/env python3
"""Save and verify the first two Linux memory-ring commands after controller info."""
import argparse
import hashlib
import json
from pathlib import Path
import re


SLOT = re.compile(r'accele160 EXPLORE ring followup event=([12]) slot=([12]) dma=0x([0-9a-f]{8}) hex=([0-9a-f]{128})')
STATUS = re.compile(r'accele160 EXPLORE ring followup event=([12]) status=([0-9a-f]{16}) lp-outbound=0x([0-9a-f]{2})')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('run', 'image', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    rom = json.loads((args.run / 'rom.json').read_text())
    qemu = (args.run / 'qemu.log').read_text(errors='replace')
    serial = (args.run / 'serial.log').read_text(errors='replace')
    if rom['image_sha256'] != hashlib.sha256(args.image.read_bytes()).hexdigest():
        raise AssertionError('image mismatch')
    if 'scsi host0: DAC960' not in serial or '__MYRS_PROBE_END__' in serial:
        raise AssertionError('wrong guest driver boundary')
    statuses = STATUS.findall(qemu)
    if len(statuses) != 2 or statuses != [('1', '0000000000000000', '00'),
                                           ('2', '0000000000000000', '00')]:
        raise AssertionError('follow-up status/ODB mismatch')
    slots = {(int(event), int(index)): (int(dma, 16), bytes.fromhex(raw))
             for event, index, dma, raw in SLOT.findall(qemu)}
    if len(slots) != 4 or slots[(1, 2)][1] != bytes(64):
        raise AssertionError('follow-up slot snapshots missing')
    first_dma, first = slots[(1, 1)]
    first_again_dma, first_again = slots[(2, 1)]
    second_dma, second = slots[(2, 2)]
    if first_dma != first_again_dma or first != first_again or second_dma != first_dma + 64:
        raise AssertionError('follow-up slot progression mismatch')
    if (first[:8] != bytes.fromhex('0200205080000000') or first[21] != 0x11 or
            first[40:44] != bytes.fromhex('80000000') or
            second[:8] != bytes.fromhex('0100205000020000') or second[21] != 0x05 or
            second[40:44] != bytes.fromhex('00020000')):
        raise AssertionError('follow-up command shape mismatch')
    result = {'gate': 'PASS', 'image_sha256': rom['image_sha256'],
              'first': {'dma': f'0x{first_dma:08x}', 'sha256': hashlib.sha256(first).hexdigest(),
                        'id': 2, 'ioctl': 0x11, 'transfer_bytes': 128,
                        'output_dma': f'0x{int.from_bytes(first[32:40], "little"):08x}'},
              'second': {'dma': f'0x{second_dma:08x}', 'sha256': hashlib.sha256(second).hexdigest(),
                         'id': 1, 'ioctl': 0x05, 'transfer_bytes': 512,
                         'output_dma': f'0x{int.from_bytes(second[32:40], "little"):08x}'},
              'status_after_both': '0000000000000000',
              'outbound_after_both': '0x00',
              'myrs_probe_complete': False,
              'scope': 'read-only bounded follow-up guest ring capture',
              'physical_card_tested': False, 'safe_to_flash': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    (args.output.parent / 'followup-slot1-64.bin').write_bytes(first)
    (args.output.parent / 'followup-slot2-64.bin').write_bytes(second)
    print('followup_slots=PASS ioctl11=True ioctl05=True no_completion=True')


if __name__ == '__main__':
    main()
