#!/usr/bin/env python3
"""Verify paired native follow-up model outputs before any guest copy."""
import argparse
import hashlib
import json
from pathlib import Path
import re

HEALTH = '67dc9bba5de17ef407a77f5e3382a7d89fcc4e7f7b4f287d7e682baece59ff32'
PDEV = '9e17de7358c0c4cb07a8a7a511c00157a17a38656412e778b69a80ca6b501a41'
ZERO128 = hashlib.sha256(bytes(128)).hexdigest()
ZERO512 = hashlib.sha256(bytes(512)).hexdigest()
SLOT = re.compile(r'ring followup event=([12]) slot=([12]) dma=0x([0-9a-f]{8}) hex=([0-9a-f]{128})')
REPORT = re.compile(r'native followup event=([12]) local-idb=0x([0-9a-f]{8}) '
                    r'marker=0x([0-9a-f]{8}) events=(\d+) slot-index=(\d+) '
                    r'slot-dma=0x([0-9a-f]{8}) digest=0x([0-9a-f]{8}) '
                    r'state=0x([0-9a-f]{8}) id=(\d+) ioctl=0x([0-9a-f]{2}) '
                    r'output=0x([0-9a-f]{8}) length=(\d+) '
                    r'status-cursor=0x([0-9a-f]{8}) completions=(\d+) '
                    r'outbound=0x([0-9a-f]{8}) reply-state=(\d+) '
                    r'dma-eoc=(\d+) status-word0=0x([0-9a-f]{8})')
MODEL = re.compile(r'native followup model event=([12]) status1=([0-9a-f]{16}) '
                   r'status2=([0-9a-f]{16}) health-sha256=([0-9a-f]{64}) '
                   r'pdev-sha256=(none|[0-9a-f]{64}) outbound=0x([0-9a-f]{8}) '
                   r'no-guest-copy=1')


def fnv(data):
    value = 0x811c9dc5
    for byte in data:
        value = ((value ^ byte) * 0x01000193) & 0xffffffff
    return value


def inspect(path, image, stage):
    qemu = (path / 'qemu.log').read_text(errors='replace')
    emu = (path / 'emu.log').read_text(errors='replace')
    serial = (path / 'serial.log').read_text(errors='replace')
    rom = json.loads((path / 'rom.json').read_text())
    if rom['image_sha256'] != hashlib.sha256(image.read_bytes()).hexdigest():
        raise AssertionError(f'{path}: image hash mismatch')
    if 'native ring mirrored output=' not in qemu or 'scsi host0: DAC960' not in serial:
        raise AssertionError(f'{path}: first-ring mirror missing')
    if 'native followup mirrored' in qemu or '__MYRS_PROBE_END__' in serial:
        raise AssertionError(f'{path}: follow-up guest copy/probe unexpectedly completed')
    slots = {(int(e), int(i)): (int(a, 16), bytes.fromhex(raw))
             for e, i, a, raw in SLOT.findall(qemu)}
    reports, models = REPORT.findall(qemu), MODEL.findall(qemu)
    if len(reports) != 2 or len(models) != 2 or (1, 1) not in slots or (2, 2) not in slots:
        raise AssertionError(f'{path}: missing paired events')
    first_addr, first = slots[(1, 1)]
    second_addr, second = slots[(2, 2)]
    if (second_addr != first_addr + 64 or first[:4] != bytes.fromhex('02002050') or
            first[21] != 0x11 or first[40:44] != bytes.fromhex('80000000') or
            second[:4] != bytes.fromhex('01002050') or second[21] != 0x05 or
            second[40:44] != bytes.fromhex('00020000')):
        raise AssertionError(f'{path}: wrong exact command shape')
    setup = bytes.fromhex(re.findall(r'lp mailbox bytes=([0-9a-f]{128})', qemu)[5])
    status_base = int.from_bytes(setup[40:48], 'little')
    expected_completions = (1, 1) if stage == 0 else (2, 2) if stage == 1 else (2, 3)
    expected_status = (('0000000000000000', '0000000000000000'),
                       ('0000000200000000', '0000000000000000'),
                       ('0000000200000000', '0000000100000000'))[stage]
    expected_health = ZERO128 if stage == 0 else HEALTH
    expected_pdev = ZERO512 if stage < 2 else PDEV
    for index, (report, model, address, slot) in enumerate(zip(
            reports, models, (first_addr, second_addr), (first, second)), 1):
        event, local, marker, count, slot_index, dma, digest, state, ident, ioctl, output, length, cursor, completions, outbound, reply_state, dma_eoc, status_word = report
        if (int(event) != index or int(local, 16) & 0x10 == 0 or
                int(marker, 16) != 0x32474e52 or int(count) != index or
                int(slot_index) != index or int(dma, 16) != address or
                int(digest, 16) != fnv(slot) or int(state, 16) != 2 or
                int(ident) != slot[0] or int(ioctl, 16) != slot[21] or
                int(output, 16) != int.from_bytes(slot[32:40], 'little') or
                int(length) != (128 if index == 1 else 512) or
                int(completions) != expected_completions[index - 1] or
                int(cursor, 16) != status_base + expected_completions[index - 1] * 8 or
                int(outbound, 16) != (0 if stage == 0 else 2)):
            raise AssertionError(f'{path}: native report mismatch: {report}')
        completed = stage >= index
        if (int(reply_state) != (3 if stage else 0) or
                int(dma_eoc) != (2 if stage else 0) or
                int(status_word, 16) != (slot[0] if completed else
                                             2 if stage else 0)):
            raise AssertionError(f'{path}: completion report mismatch: {report}')
        m_event, status1, status2, health, pdev, m_outbound = model
        if (int(m_event) != index or status1 !=
                (expected_status[0] if stage >= 1 else '0000000000000000') or
                status2 != (expected_status[1] if stage >= 2 and index == 2
                            else '0000000000000000') or
                health != expected_health or
                pdev != ('none' if index == 1 else expected_pdev) or
                int(m_outbound, 16) != (0 if stage == 0 else 2)):
            raise AssertionError(f'{path}: model data mismatch: {model}')
    health_dma = int.from_bytes(first[32:40], 'little')
    pdev_dma = int.from_bytes(second[32:40], 'little')
    if stage >= 1 and not re.search(
            rf'mu-dma1-native-ring-health descriptor=[0-9a-f]{{8}} '
            rf'local=[0-9a-f]{{8}} host={health_dma:08x} bytes=128 eoc=1', emu):
        raise AssertionError(f'{path}: no native health DMA1 EOC')
    if stage >= 2 and not re.search(
            rf'mu-dma1-native-ring-pdev descriptor=[0-9a-f]{{8}} '
            rf'local=[0-9a-f]{{8}} host={pdev_dma:08x} bytes=512 eoc=1', emu):
        raise AssertionError(f'{path}: no native pdev DMA1 EOC')
    return {'image_sha256': rom['image_sha256'], 'stage': stage,
            'health_dma': f'0x{health_dma:08x}',
            'pdev_dma': f'0x{pdev_dma:08x}',
            'completions': expected_completions,
            'health_sha256': expected_health, 'pdev_sha256': expected_pdev,
            'followup_guest_mirror': False, 'myrs_probe_complete': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('observer-run', 'health-run', 'pdev-run', 'observer-image',
                 'health-image', 'pdev-image', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    receipt = {'gate': 'PASS',
               'observer': inspect(a.observer_run, a.observer_image, 0),
               'health': inspect(a.health_run, a.health_image, 1),
               'pdev': inspect(a.pdev_run, a.pdev_image, 2),
               'physical_card_tested': False, 'safe_to_flash': False}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(receipt, indent=2) + '\n')
    print('native_followup_model=PASS observer_health_pdev=True guest_mirror=False')


if __name__ == '__main__':
    main()
