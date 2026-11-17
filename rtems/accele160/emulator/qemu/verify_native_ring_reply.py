#!/usr/bin/env python3
"""Check paired native first-ring reply in model memory, without guest mirroring."""
import argparse
import hashlib
import json
from pathlib import Path
import re


SLOT = re.compile(r'accele160 EXPLORE memory-mailbox slot dma=0x([0-9a-f]{16}) hex=([0-9a-f]{128})')
STAGED = re.compile(r'checkpoint memory-mailbox-slot dma=([0-9a-f]{16}) bytes=([0-9a-f]{128}) staged=1 completion=unmodeled')
REPORT = re.compile(r'accele160 EXPLORE native ring observer marker=0x([0-9a-f]{8}) state=0x([0-9a-f]{8}) digest=0x([0-9a-f]{8}) cursor=0x([0-9a-f]{8}) output=0x([0-9a-f]{8}) length=([0-9]+) id=([0-9]+) seen-idb=0x([0-9a-f]{8}) completions=([0-9]+) output-digest=0x([0-9a-f]{8}) dma-status=0x([0-9a-f]{8}) status-id=([0-9]+) residual=0x([0-9a-f]{8})')
MODEL = re.compile(r'accele160 EXPLORE ring model phase=([^ ]+) slot-word0=0x([0-9a-f]{8}) status=([0-9a-f]{16}) output-sha256=([0-9a-f]{64})')
GUEST = re.compile(r'accele160 EXPLORE ring guest phase=([^ ]+) status=([0-9a-f]{16}) health-first=([0-9a-f]{16}) output-sha256=([0-9a-f]{64})')


def fnv1a(data):
    digest = 0x811c9dc5
    for value in data:
        digest = ((digest ^ value) * 0x01000193) & 0xffffffff
    return digest


def single(pattern, source, label):
    found = pattern.findall(source)
    if len(found) != 1:
        raise AssertionError(f'{label}: expected one, found {len(found)}')
    return found[0]


def run(path, image, response):
    rom = json.loads((path / 'rom.json').read_text())
    qemu = (path / 'qemu.log').read_text(errors='replace')
    emu = (path / 'emu.log').read_text(errors='replace')
    if rom['image_sha256'] != hashlib.sha256(image.read_bytes()).hexdigest():
        raise AssertionError(f'{path}: wrong image SHA')
    if [x['ioctl'] for x in rom['mailbox_requests'][:6]] != [1, 0x11, 0x15, 0xd0, 0x2d, 0x8e]:
        raise AssertionError(f'{path}: wrong setup sequence')
    dma, slot_hex = single(SLOT, qemu, f'{path} slot')
    if (dma, slot_hex) != single(STAGED, emu, f'{path} model staging'):
        raise AssertionError(f'{path}: guest/model slot mismatch')
    slot = bytes.fromhex(slot_hex)
    output_bus = int.from_bytes(slot[32:40], 'little')
    fields = single(REPORT, qemu, f'{path} report')
    numbers = [int(value, 10) if i in (5, 6, 8, 11) else int(value, 16)
               for i, value in enumerate(fields)]
    if numbers[:3] != [0x31474e52, 3 if response else 2, fnv1a(slot)]:
        raise AssertionError(f'{path}: observer marker/state/slot digest mismatch')
    if numbers[4:8] != [output_bus, 1004, 1, 0x10]:
        raise AssertionError(f'{path}: output request or IDB10 mismatch')
    expected_cursor = int(dma, 16) + (64 if response else 0)
    if numbers[3] != expected_cursor:
        raise AssertionError(f'{path}: command cursor mismatch')
    model, guest = MODEL.findall(qemu), GUEST.findall(qemu)
    if len(model) != 2 or len(guest) != 2 or model[0][0] != 'before-idb10' or model[1][0] != 'after-5m':
        raise AssertionError(f'{path}: missing model/guest snapshots')
    if model[0][1:] != ('50200001', '0000000000000000',
                        'fa16c3b03c75c0d2a74b01ab8bd3806b53f82abc36bbcc29ae987898f56f5544'):
        raise AssertionError(f'{path}: wrong initial model state')
    if guest[0][1:] != guest[1][1:] or guest[0][1] != '0000000000000000':
        raise AssertionError(f'{path}: QEMU guest memory was modified')
    output_hex = single(re.compile(r'accele160 EXPLORE ring model output-hex=([0-9a-f]{2008})'),
                        qemu, f'{path} model output')
    output = bytes.fromhex(output_hex)
    if hashlib.sha256(output).hexdigest() != model[1][3]:
        raise AssertionError(f'{path}: model output/hash mismatch')
    outbound = single(re.compile(r'accele160 EXPLORE native ring outbound=0x([0-9a-f]{8}) no-guest-mirror=1'),
                      qemu, f'{path} outbound')
    dma_copy = 'checkpoint mu-dma1-native-ring-output' in emu
    if response:
        if (numbers[8:] != [1, fnv1a(output), 2, 1, 0xffffffec] or
                model[1][1:3] != ('00000000', '00000001ffffffec') or
                int(outbound, 16) != 2 or not dma_copy):
            raise AssertionError(f'{path}: native ring completion mismatch')
    elif (numbers[8:] != [0, 0, 0, 0, 0] or model[1][1:] != model[0][1:] or
          int(outbound, 16) != 0 or dma_copy):
        raise AssertionError(f'{path}: old observer unexpectedly completed')
    return {'image_sha256': rom['image_sha256'], 'slot_dma': f'0x{dma}',
            'slot_sha256': hashlib.sha256(slot).hexdigest(),
            'model_status_words': model[1][2],
            'model_output_sha256': model[1][3],
            'outbound': f'0x{int(outbound, 16):08x}',
            'dma1_copy_observed': dma_copy,
            'guest_unchanged': True,
            'output_bytes': output}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('observer-run', 'reply-run', 'observer-image', 'reply-image',
                 'stock-output', 'stock-status', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    observer = run(args.observer_run, args.observer_image, False)
    reply = run(args.reply_run, args.reply_image, True)
    old_bytes, new_bytes = observer.pop('output_bytes'), reply.pop('output_bytes')
    stock_output = args.stock_output.read_bytes()
    stock_status = args.stock_status.read_bytes()
    if new_bytes != stock_output or len(old_bytes) != 1004 or any(old_bytes) or stock_status != bytes.fromhex('01000000ecffffff'):
        raise AssertionError('native response differs from captured stock fixture')
    receipt = {'gate': 'PASS', 'observer': observer, 'reply': reply,
               'stock_output_equal': True,
               'stock_status_bytes': stock_status.hex(),
               'scope': 'opt-in native first-ring model reply, no guest mirroring',
               'physical_card_tested': False, 'safe_to_flash': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + '\n')
    (args.output.parent / 'native-output-1004.bin').write_bytes(new_bytes)
    (args.output.parent / 'native-status-8.bin').write_bytes(stock_status)
    print('native_ring_reply=PASS stock_equal=True guest_unchanged=True')


if __name__ == '__main__':
    main()
