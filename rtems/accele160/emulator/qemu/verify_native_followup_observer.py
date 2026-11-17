#!/usr/bin/env python3
"""Verify paired native read-only observers for the next two Linux ring slots."""
import argparse
import hashlib
import json
from pathlib import Path
import re


SLOT = re.compile(r'accele160 EXPLORE ring followup event=([12]) slot=([12]) dma=0x([0-9a-f]{8}) hex=([0-9a-f]{128})')
STATUS = re.compile(r'accele160 EXPLORE ring followup event=([12]) status=([0-9a-f]{16}) lp-outbound=0x([0-9a-f]{2})')
REPORT = re.compile(r'accele160 EXPLORE native followup event=([12]) local-idb=0x([0-9a-f]{8}) marker=0x([0-9a-f]{8}) events=([0-9]+) slot-index=([0-9]+) slot-dma=0x([0-9a-f]{8}) digest=0x([0-9a-f]{8}) state=0x([0-9a-f]{8}) id=([0-9]+) ioctl=0x([0-9a-f]{2}) output=0x([0-9a-f]{8}) length=([0-9]+) status-cursor=0x([0-9a-f]{8}) completions=([0-9]+) outbound=0x([0-9a-f]{8})')
SETUP = re.compile(r'accele160 EXPLORE native set-mbox completion id=1 status=0x0000 data=0x00000420 no-dma=1')


def fnv1a(data):
    value = 0x811c9dc5
    for byte in data:
        value = ((value ^ byte) * 0x01000193) & 0xffffffff
    return value


def inspect(path, image, observed):
    rom = json.loads((path / 'rom.json').read_text())
    qemu = (path / 'qemu.log').read_text(errors='replace')
    serial = (path / 'serial.log').read_text(errors='replace')
    if rom['image_sha256'] != hashlib.sha256(image.read_bytes()).hexdigest() or len(SETUP.findall(qemu)) != 1:
        raise AssertionError(f'{path}: image/setup mismatch')
    if [x['ioctl'] for x in rom['mailbox_requests'][:6]] != [1, 0x11, 0x15, 0xd0, 0x2d, 0x8e]:
        raise AssertionError(f'{path}: request sequence mismatch')
    mailboxes = re.findall(r'accele160 lp mailbox bytes=([0-9a-f]{128})', qemu)
    if len(mailboxes) != 6:
        raise AssertionError(f'{path}: missing sixth mailbox bytes')
    setup = bytes.fromhex(mailboxes[5])
    status_cursor = int.from_bytes(setup[40:44], 'little') + 8
    if 'native ring mirrored output=' not in qemu or 'scsi host0: DAC960' not in serial:
        raise AssertionError(f'{path}: first-ring mirror absent')
    statuses = STATUS.findall(qemu)
    if statuses != [('1', '0000000000000000', '00'),
                    ('2', '0000000000000000', '00')]:
        raise AssertionError(f'{path}: unexpected status or LP ODB')
    slots = {(int(e), int(i)): (int(a, 16), bytes.fromhex(raw))
             for e, i, a, raw in SLOT.findall(qemu)}
    reports = REPORT.findall(qemu)
    if len(slots) != 4 or len(reports) != 2:
        raise AssertionError(f'{path}: missing slot/report')
    if slots[(1, 2)][1] != bytes(64) or slots[(2, 1)] != slots[(1, 1)]:
        raise AssertionError(f'{path}: guest slot progression mismatch')
    first_addr, first = slots[(1, 1)]
    second_addr, second = slots[(2, 2)]
    if (second_addr != first_addr + 64 or first[0:4] != bytes.fromhex('02002050') or
            first[21] != 0x11 or first[40:44] != bytes.fromhex('80000000') or
            second[0:4] != bytes.fromhex('01002050') or second[21] != 0x05 or
            second[40:44] != bytes.fromhex('00020000')):
        raise AssertionError(f'{path}: wrong observed command shape')
    decoded = []
    for index, (fields, address, slot) in enumerate(zip(reports, (first_addr, second_addr),
                                                        (first, second)), 1):
        event, local, marker, events, slot_index, slot_dma, digest, state, ident, ioctl, output, length, cursor, completions, outbound = fields
        if (int(event) != index or not int(local, 16) & 0x10 or
                int(outbound, 16) != 0 or
                int(completions) != (1 if observed else 0)):
            raise AssertionError(f'{path}: notification/status mismatch')
        if observed:
            if (int(marker, 16) != 0x32474e52 or int(events) != index or
                    int(slot_index) != index or int(slot_dma, 16) != address or
                    int(digest, 16) != fnv1a(slot) or int(state, 16) != 2 or
                    int(ident) != slot[0] or int(ioctl, 16) != slot[21] or
                    int(output, 16) != int.from_bytes(slot[32:40], 'little') or
                    int(length) != (128 if index == 1 else 512) or
                    int(cursor, 16) != status_cursor):
                raise AssertionError(f'{path}: native follow-up report mismatch')
        elif int(marker, 16) != 0 or int(events) != 0 or int(state, 16) != 0:
            raise AssertionError(f'{path}: old image unexpectedly observed follow-up')
        decoded.append({'dma': f'0x{address:08x}',
                        'sha256': hashlib.sha256(slot).hexdigest(),
                        'id': slot[0], 'ioctl': slot[21],
                        'output_dma': f'0x{int.from_bytes(slot[32:40], "little"):08x}',
                        'length': 128 if index == 1 else 512})
    if '__MYRS_PROBE_END__' in serial:
        raise AssertionError(f'{path}: unexpected completed Linux probe')
    return {'image_sha256': rom['image_sha256'], 'slots': decoded,
            'observed': observed, 'new_ring_completion': False,
            'myrs_probe_complete': False}


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
               'scope': 'two read-only native follow-up command observations',
               'physical_card_tested': False, 'safe_to_flash': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + '\n')
    print('native_followup_observer=PASS events=2 no_new_completion=True')


if __name__ == '__main__':
    main()
