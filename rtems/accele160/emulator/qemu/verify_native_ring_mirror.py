#!/usr/bin/env python3
"""Check strict opt-in first native ring guest mirror and old-image rejection."""
import argparse
import hashlib
import json
from pathlib import Path
import re


GUEST = re.compile(r'accele160 EXPLORE ring guest phase=([^ ]+) status=([0-9a-f]{16}) health-first=([0-9a-f]{16}) output-sha256=([0-9a-f]{64})')
MIRROR = re.compile(r'accele160 EXPLORE native ring mirrored output=0x([0-9a-f]+) bytes=1004 sha256=([0-9a-f]{64}) status=01000000ecffffff slot-word0=0 outbound=0x02 irq=1')


def check(path, image, success, stock_sha):
    rom = json.loads((path / 'rom.json').read_text())
    qemu = (path / 'qemu.log').read_text(errors='replace')
    serial = (path / 'serial.log').read_text(errors='replace')
    if rom['image_sha256'] != hashlib.sha256(image.read_bytes()).hexdigest():
        raise AssertionError(f'{path}: image mismatch')
    if [x['ioctl'] for x in rom['mailbox_requests'][:6]] != [1, 0x11, 0x15, 0xd0, 0x2d, 0x8e]:
        raise AssertionError(f'{path}: wrong setup sequence')
    guests = GUEST.findall(qemu)
    mirrors = MIRROR.findall(qemu)
    if len(guests) != (3 if success else 2) or len(mirrors) != (1 if success else 0):
        raise AssertionError(f'{path}: mirror/guest snapshot count mismatch')
    if guests[0][0] != 'before-idb10' or guests[1][0] != 'after-5m' or guests[0][1:] != guests[1][1:]:
        raise AssertionError(f'{path}: guest changed before guarded mirror')
    if success:
        if (guests[2] != ('after-mirror', '01000000ecffffff',
                          '0000000000000000', stock_sha) or
                mirrors[0][1] != stock_sha or
                'accele160 bar0 W offset=0x002c size=1 value=0x03' not in qemu or
                qemu.count('accele160 bar0 W offset=0x0020 size=1 value=0x10') < 2 or
                'scsi host0: Configuring AcceleRAID 160 PCI RAID Controller' not in serial or
                'scsi host0: DAC960' not in serial):
            raise AssertionError(f'{path}: Linux did not register the SCSI host')
    else:
        if ('native ring mirror rejected: report/doorbell/DMA state' not in qemu or
                'scsi host0: Configuring AcceleRAID 160 PCI RAID Controller' in serial):
            raise AssertionError(f'{path}: old observer unexpectedly registered host')
    if '__MYRS_PROBE_END__' in serial or 'module=myrs insmod_status=0' in serial:
        raise AssertionError(f'{path}: unexpected completed module probe')
    return {'image_sha256': rom['image_sha256'],
            'mirror_performed': success,
            'guest_status_after_mirror': guests[2][1] if success else None,
            'guest_output_sha256_after_mirror': guests[2][3] if success else None,
            'linux_scsi_host_registered': success,
            'myrs_probe_end': False,
            'myrs_module_load_complete': False,
            'subsequent_idb10_observed': success}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('negative-run', 'positive-run', 'negative-image', 'positive-image',
                 'stock-output', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    stock_sha = hashlib.sha256(args.stock_output.read_bytes()).hexdigest()
    receipt = {'gate': 'PASS',
               'negative': check(args.negative_run, args.negative_image, False, stock_sha),
               'positive': check(args.positive_run, args.positive_image, True, stock_sha),
               'scope': 'strict opt-in native first-ring guest mirror and SCSI host registration',
               'next_boundary': 'subsequent memory-ring commands not yet modeled',
               'physical_card_tested': False, 'safe_to_flash': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + '\n')
    print('native_ring_mirror=PASS old_pending=True scsi_host_registered=True probe_incomplete=True')


if __name__ == '__main__':
    main()
