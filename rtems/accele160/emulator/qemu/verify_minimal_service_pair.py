#!/usr/bin/env python3
"""Compare marker-instrumented and uninstrumented four-ring guest runs."""
import argparse
import hashlib
import json
from pathlib import Path
import re


FIRST = re.compile(r'native ring mirrored output=0x[0-9a-f]{8} bytes=(\d+) '
                   r'sha256=([0-9a-f]{64}) status=([0-9a-f]{16}) '
                   r'slot-word0=0 outbound=0x02 irq=1')
FOLLOW = re.compile(r'native followup mirrored event=([12]) output=0x[0-9a-f]{8} '
                    r'bytes=(\d+) sha256=([0-9a-f]{64}) status=([0-9a-f]{16}) '
                    r'slot-word0=0 outbound=0x02 irq=1')
NEXT = re.compile(r'native next mirrored event=(3) output=0x[0-9a-f]{8} '
                  r'bytes=(\d+) sha256=([0-9a-f]{64}) status=([0-9a-f]{16}) '
                  r'slot-word0=0 outbound=0x02 irq=1')
EXPECTED = [
    ('slot0', '1004', 'a3f72f98e18667d7c80eebac996b77f465bce5d5024a8b3ec3c70d2a285572f8', '01000000ecffffff'),
    ('slot1', '128', '67dc9bba5de17ef407a77f5e3382a7d89fcc4e7f7b4f287d7e682baece59ff32', '0200000000000000'),
    ('slot2', '512', '9e17de7358c0c4cb07a8a7a511c00157a17a38656412e778b69a80ca6b501a41', '0100000000000000'),
    ('slot3', '1004', 'a3f72f98e18667d7c80eebac996b77f465bce5d5024a8b3ec3c70d2a285572f8', '01000000ecffffff'),
]


def inspect(directory, image):
    qemu = (directory / 'qemu.log').read_text(errors='replace')
    serial = (directory / 'serial.log').read_text(errors='replace')
    rom = json.loads((directory / 'rom.json').read_text())
    digest = hashlib.sha256(image.read_bytes()).hexdigest()
    if rom['image_sha256'] != digest:
        raise AssertionError(f'{directory}: wrong image')
    first, follow, later = FIRST.findall(qemu), FOLLOW.findall(qemu), NEXT.findall(qemu)
    if len(first) != 1 or len(follow) != 2 or len(later) != 1:
        raise AssertionError(f'{directory}: mirror count')
    records = [('slot0', *first[0])]
    records.extend((f'slot{event}', length, sha, status)
                   for event, length, sha, status in follow)
    records.extend((f'slot{event}', length, sha, status)
                   for event, length, sha, status in later)
    if records != EXPECTED:
        raise AssertionError(f'{directory}: stock output/status mismatch')
    if ('native next mirrored event=4' in qemu or
            'native next event=4' not in qemu or
            'lp reset requested; unmodeled' not in qemu or
            '__MYRS_PROBE_END__' in serial or
            'module=myrs insmod_status=0' in serial):
        raise AssertionError(f'{directory}: SCSI boundary changed')
    return {'image_sha256': digest,
            'rom_mailbox_ioctls': [x['ioctl'] for x in rom['mailbox_requests']],
            'mirrored': [{'slot': slot, 'bytes': int(length), 'sha256': sha,
                          'status_hex': status} for slot, length, sha, status in records],
            'slot4_observed': True, 'slot4_completed': False,
            'linux_reset_requested': True, 'myrs_probe_complete': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('service-run', 'control-run', 'service-image', 'control-image', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    service = inspect(args.service_run, args.service_image)
    control = inspect(args.control_run, args.control_image)
    if service['rom_mailbox_ioctls'] != control['rom_mailbox_ioctls'] or (
            service['mirrored'] != control['mirrored']):
        raise AssertionError('instrumented service differs from control')
    receipt = {'gate': 'PASS', 'service': service, 'control': control,
               'physical_card_tested': False, 'safe_to_flash': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + '\n')
    print('minimal_service_pair=PASS four_stock_replies=True scsi_reply=False')


if __name__ == '__main__':
    main()
