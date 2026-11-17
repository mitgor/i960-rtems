#!/usr/bin/env python3
"""Verify paired native SET_MEM_MBOX QEMU runs without treating a model reply as hardware."""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED = [0x01, 0x11, 0x15, 0xd0, 0x2d, 0x8e]
COMPLETION = ('accele160 EXPLORE native set-mbox completion '
              'id=1 status=0x0000 data=0x00000420 no-dma=1')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check_run(path, image, completed):
    rom = json.loads((path / 'rom.json').read_text())
    log = (path / 'qemu.log').read_text(errors='replace')
    packet = bytes.fromhex(rom['mailbox_bytes_hex'][5])
    if [x['ioctl'] for x in rom['mailbox_requests'][:6]] != EXPECTED:
        raise AssertionError(f'{path}: six-command sequence missing')
    if len(packet) != 64 or packet[:8] != bytes.fromhex('0100204020040000') or \
            packet[21:23] != bytes.fromhex('8e01'):
        raise AssertionError(f'{path}: SET_MEM_MBOX command shape changed')
    if rom['image_sha256'] != sha(image.read_bytes()):
        raise AssertionError(f'{path}: wrong image')
    if len([x for x in log.splitlines() if x.startswith(
            'accele160 EXPLORE native firmware completion ')]) != 5:
        raise AssertionError(f'{path}: five ROM completions missing')
    if 'synthetic IOCTL completion' in log or 'stock firmware completion' in log:
        raise AssertionError(f'{path}: nonnative completion present')
    if (log.count(COMPLETION) == 1) != completed:
        raise AssertionError(f'{path}: unexpected sixth native completion')
    if completed:
        if 'accele160 bar0 W offset=0x0020 size=1 value=0x10' not in log:
            raise AssertionError(f'{path}: guest did not advance to MMBOX_NEW_CMD')
    else:
        if 'accele160 EXPLORE native set-mbox pending after bounded i960 steps' not in log:
            raise AssertionError(f'{path}: missing bounded pending observation')
        if 'accele160 bar0 W offset=0x0020 size=1 value=0x10' in log:
            raise AssertionError(f'{path}: guest advanced without completion')
    return {'image_sha256': rom['image_sha256'],
            'sixth_mailbox_sha256': sha(packet),
            'sixth_state': 'completed' if completed else 'pending'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--old-run', type=Path, required=True)
    p.add_argument('--new-run', type=Path, required=True)
    p.add_argument('--old-image', type=Path, required=True)
    p.add_argument('--new-image', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    receipt = {'gate': 'PASS',
               'old': check_run(args.old_run, args.old_image, False),
               'new': check_run(args.new_run, args.new_image, True),
               'scope': 'opt-in exploratory QEMU/i960 model',
               'physical_card_tested': False, 'safe_to_flash': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + '\n')
    print('native_set_mbox_pair=PASS')


if __name__ == '__main__':
    main()
