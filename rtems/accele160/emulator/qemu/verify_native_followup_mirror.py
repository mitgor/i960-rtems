#!/usr/bin/env python3
"""Verify strict native follow-up guest mirrors and the next bounded boundary."""
import argparse
import hashlib
import json
from pathlib import Path
import re

HEALTH = '67dc9bba5de17ef407a77f5e3382a7d89fcc4e7f7b4f287d7e682baece59ff32'
PDEV = '9e17de7358c0c4cb07a8a7a511c00157a17a38656412e778b69a80ca6b501a41'
MIRROR = re.compile(r'native followup mirrored event=([12]) output=0x([0-9a-f]{8}) '
                    r'bytes=(\d+) sha256=([0-9a-f]{64}) status=([0-9a-f]{16}) '
                    r'slot-word0=0 outbound=0x02 irq=1')
SLOT = re.compile(r'ring followup event=([1-4]) slot=([1-4]) '
                  r'dma=0x([0-9a-f]{8}) hex=([0-9a-f]{128})')


def inspect(path, image, expected_mirrors, boundary=False):
    qemu = (path / 'qemu.log').read_text(errors='replace')
    serial = (path / 'serial.log').read_text(errors='replace')
    rom = json.loads((path / 'rom.json').read_text())
    if rom['image_sha256'] != hashlib.sha256(image.read_bytes()).hexdigest():
        raise AssertionError(f'{path}: image hash mismatch')
    if 'native ring mirrored output=' not in qemu or 'scsi host0: DAC960' not in serial:
        raise AssertionError(f'{path}: initial native ring mirror missing')
    mirrors = MIRROR.findall(qemu)
    if len(mirrors) != expected_mirrors or [int(m[0]) for m in mirrors] != list(range(1, expected_mirrors + 1)):
        raise AssertionError(f'{path}: wrong mirror count/order')
    slots = {(int(e), int(i)): (int(a, 16), bytes.fromhex(raw))
             for e, i, a, raw in SLOT.findall(qemu)}
    decoded = []
    for event, bus, length, digest, status in mirrors:
        index = int(event)
        slot_bus, slot = slots[(index, index)]
        want = (128, HEALTH, '0200000000000000') if index == 1 else (
            512, PDEV, '0100000000000000')
        if ((int(length), digest, status) != want or
                int(bus, 16) != int.from_bytes(slot[32:40], 'little') or
                slot_bus != slots[(1, 1)][0] + (index - 1) * 64 or
                f'native followup guest-mirror accepted event={index}' not in qemu):
            raise AssertionError(f'{path}: mirror differs from native slot/stock fixture')
        decoded.append({'event': index, 'output_dma': f'0x{int(bus, 16):08x}',
                        'bytes': int(length), 'sha256': digest, 'status_hex': status})
    for index in range(expected_mirrors + 1, 3):
        if f'native followup guest-mirror rejected event={index}' not in qemu:
            raise AssertionError(f'{path}: missing negative control event {index}')
    if '__MYRS_PROBE_END__' in serial or 'module=myrs insmod_status=0' in serial:
        raise AssertionError(f'{path}: unexpectedly completed myrs probe')
    result = {'image_sha256': rom['image_sha256'],
              'mirrored': decoded, 'myrs_probe_complete': False}
    if boundary:
        for event in (3, 4):
            if (event, event) not in slots or (
                    f'ring followup event={event} beyond bounded two-slot model; '
                    'no i960 doorbell or guest copy') not in qemu:
                raise AssertionError(f'{path}: missing bounded next-command capture')
        third_addr, third = slots[(3, 3)]
        fourth_addr, fourth = slots[(4, 4)]
        if (third_addr != slots[(1, 1)][0] + 128 or
                fourth_addr != third_addr + 64 or
                third[:4] != bytes.fromhex('01002050') or
                third[4:8] != bytes.fromhex('ec030000') or third[21] != 1 or
                third[40:44] != bytes.fromhex('ec030000') or
                fourth[1:4] != bytes.fromhex('010210') or
                fourth[4:8] != bytes.fromhex('24000000') or
                fourth[40:44] != bytes.fromhex('24000000')):
            raise AssertionError(f'{path}: next slot shapes changed')
        result['next_boundary'] = {
            'host_idb10_events': [3, 4], 'model_i960_doorbell': False,
            'model_completion': False,
            'slots': [{'index': 3, 'dma': f'0x{third_addr:08x}',
                       'sha256': hashlib.sha256(third).hexdigest(),
                       'word0': f'0x{int.from_bytes(third[:4], "little"):08x}',
                       'output_dma': f'0x{int.from_bytes(third[32:40], "little"):08x}',
                       'length': int.from_bytes(third[40:44], 'little')},
                      {'index': 4, 'dma': f'0x{fourth_addr:08x}',
                       'sha256': hashlib.sha256(fourth).hexdigest(),
                       'word0': f'0x{int.from_bytes(fourth[:4], "little"):08x}',
                       'field_08_15': f'0x{int.from_bytes(fourth[8:16], "little"):016x}',
                       'output_dma': f'0x{int.from_bytes(fourth[32:40], "little"):08x}',
                       'length': int.from_bytes(fourth[40:44], 'little')}]}
        return result, third, fourth
    return result, None, None


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('observer-run', 'health-run', 'pdev-run', 'observer-image',
                 'health-image', 'pdev-image', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    old, _, _ = inspect(a.observer_run, a.observer_image, 0)
    health, _, _ = inspect(a.health_run, a.health_image, 1)
    pdev, third, fourth = inspect(a.pdev_run, a.pdev_image, 2, True)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    (a.output.parent / 'slot3-64.bin').write_bytes(third)
    (a.output.parent / 'slot4-64.bin').write_bytes(fourth)
    a.output.write_text(json.dumps({
        'gate': 'PASS', 'observer': old, 'health': health, 'pdev': pdev,
        'physical_card_tested': False, 'safe_to_flash': False}, indent=2) + '\n')
    print('native_followup_mirror=PASS negative_health_full=True next_boundary=slots3,4')


if __name__ == '__main__':
    main()
