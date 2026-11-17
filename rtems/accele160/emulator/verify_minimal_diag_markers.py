#!/usr/bin/env python3
"""Check sampled early native entry markers in pinned offline images."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile


def sample(emulator, image, cycles):
    with tempfile.TemporaryDirectory(prefix='accele160-marker-') as directory:
        aperture = Path(directory) / 'aperture.bin'
        command = [str(emulator.resolve()), str(image.resolve()), str(cycles),
                   '--board-id=11', '--quiet-trace',
                   f'--dump-aperture={aperture}']
        with (Path(directory) / 'run.log').open('w') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode != 0:
            raise AssertionError(f'emulator stopped before cycle {cycles}')
        data = aperture.read_bytes()
        if len(data) != 8192:
            raise AssertionError('wrong aperture size')
        words = struct.unpack_from('<16I', data, 0x1f00)
        return {'cycles': cycles, 'stage2': f'{words[0]:08x}',
                'stage2_result': f'{words[1]:08x}',
                'marker': f'{words[7]:08x}', 'host_marker': f'{words[9]:08x}',
                'worker_count': words[4], 'done': words[6],
                'report_words': [f'{x:08x}' for x in words]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('emulator', 'passive-image', 'service-image',
                 'old-service-image', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    cases = {
        'passive': (args.passive_image, [(1354528, '00000000'),
                                        (1485706, '30544e45'),
                                        (1485711, '31544e45'),
                                        (1600000, '5254454d'),
                                        (1700000, '50415353')]),
        'service': (args.service_image, [(1500000, '00000000'),
                                        (1535710, '30544e45'),
                                        (1535715, '31544e45'),
                                        (1650000, '5254454d'),
                                        (1700000, '50415353')]),
        'old_service': (args.old_service_image, [(1535710, '00000000'),
                                                (1535715, '00000000'),
                                                (1700000, '50415353')]),
    }
    observations = {}
    for label, (image, checkpoints) in cases.items():
        records = []
        for cycles, expected in checkpoints:
            got = sample(args.emulator, image, cycles)
            if got['marker'] != expected or got['stage2'] != '32544753':
                raise AssertionError(f'{label} at {cycles}: {got}')
            records.append(got)
        observations[label] = {'image_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                               'checkpoints': records}
    for label in ('passive', 'service', 'old_service'):
        final = observations[label]['checkpoints'][-1]
        if (final['stage2_result'] != '00002000' or
                final['host_marker'] != '30545348' or
                final['worker_count'] != 64 or final['done'] != 1):
            raise AssertionError(f'{label} failed scheduler/host observer')
    new = observations['service']['checkpoints'][-1]['report_words']
    old = observations['old_service']['checkpoints'][-1]['report_words']
    if any(new[i] != old[i] for i in range(16) if i not in (2, 3)):
        raise AssertionError('instrumented service changed final report fields')
    receipt = {'gate': 'PASS', 'scope': 'exploratory i960 entry/report sampling',
               'emulator_sha256': hashlib.sha256(args.emulator.read_bytes()).hexdigest(),
               'observations': observations, 'physical_card_tested': False,
               'safe_to_flash': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + '\n')
    print('minimal_diag_markers=PASS')


if __name__ == '__main__':
    main()
