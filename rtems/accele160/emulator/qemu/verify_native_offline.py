#!/usr/bin/env python3
"""Run the five-reply native ROM and Linux guest gates without hardware access."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
FIXTURES = ROOT / 'artifacts/current'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(command, log):
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    log.write_text('command=' + ' '.join(map(str, command)) + '\n' +
                   result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f'{log.name} failed with exit {result.returncode}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('emulator', 'qemu', 'image', 'stock', 'bios', 'linux-iso', 'output-dir'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--linux-seconds', type=float, default=110)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    image = args.image.resolve()
    stock = args.stock.resolve()
    candidate_bytes, stock_bytes = image.read_bytes(), stock.read_bytes()
    if len(candidate_bytes) != 0x100000 or len(stock_bytes) != 0x100000:
        raise AssertionError('expected exact 1 MiB stock and candidate')
    if sha(stock_bytes) != '0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943':
        raise AssertionError('wrong second-spare stock base')
    changed = [i for i, (before, after) in enumerate(zip(stock_bytes, candidate_bytes))
               if before != after]
    if not changed or any(not 0x40000 <= i < 0xc0000 for i in changed):
        raise AssertionError('candidate differs outside bounded firmware region')
    fixture_dir = FIXTURES / 'accele160-stock-ioctl11-20261116'
    fixture_2d_dir = FIXTURES / 'accele160-stock-ioctl2d-20261116'
    desc = candidate_bytes[0xe0000:0xe0200]
    if desc != (fixture_2d_dir / 'stock-ioctl-2d.bin').read_bytes():
        raise AssertionError('candidate descriptor differs from stock IOCTL 0x2d')
    direct = ROOT / 'rtems/accele160/emulator/test_native_ioctl11_gate.py'
    direct_base = [sys.executable, str(direct), '--emulator', str(args.emulator.resolve()),
                   '--image', str(image), '--first-fixture', str(FIXTURES /
                   'accele160-offline-build-20261115/first-controller-info-fixture.json'),
                   '--first-reply', str(FIXTURES /
                   'accele160-offline-build-20261115/stock-get-ctlr-info-reply.bin'),
                   '--second-fixture', str(fixture_dir / 'ioctl11-fixture.json'),
                   '--third-fixture', str(fixture_dir / 'ioctl15-fixture.json'),
                   '--fourth-fixture', str(fixture_dir / 'ioctld0-fixture.json'),
                   '--fifth-fixture', str(fixture_2d_dir / 'ioctl2d-fixture.json')]
    run(direct_base + ['--output', str(out / 'direct-valid.json')],
        out / 'direct-valid.log')
    run(direct_base + ['--corrupt-fifth-length', '--output',
                       str(out / 'direct-invalid.json')], out / 'direct-invalid.log')
    coupled = ROOT / 'rtems/accele160/emulator/qemu/test_native_rom_coupled.py'
    run([sys.executable, str(coupled), '--emulator', str(args.emulator.resolve()),
         '--qemu', str(args.qemu.resolve()), '--image', str(image),
         '--bios', str(args.bios.resolve()),
         '--request-fixture', str(FIXTURES /
         'accele160-offline-build-20261115/first-controller-info-fixture.json'),
         '--second-fixture', str(fixture_dir / 'ioctl11-fixture.json'),
         '--third-fixture', str(fixture_dir / 'ioctl15-fixture.json'),
         '--fourth-fixture', str(fixture_dir / 'ioctld0-fixture.json'),
         '--fifth-fixture', str(fixture_2d_dir / 'ioctl2d-fixture.json'),
         '--output-dir', str(out / 'coupled'), '--seconds', '15'],
        out / 'coupled.log')
    guest = ROOT / 'rtems/accele160/emulator/qemu/test_native_linux_guest.py'
    run([sys.executable, str(guest), '--emulator', str(args.emulator.resolve()),
         '--qemu', str(args.qemu.resolve()), '--image', str(image),
         '--bios', str(args.bios.resolve()), '--linux-iso',
         str(args.linux_iso.resolve()), '--output-dir', str(out / 'linux'),
         '--seconds', str(args.linux_seconds)], out / 'linux.log')
    receipt = {
        'gate': 'PASS', 'image_sha256': sha(candidate_bytes),
        'stock_sha256': sha(stock_bytes), 'changed_bytes': len(changed),
        'changed_min': min(changed), 'changed_max': max(changed),
        'descriptor_sha256': sha(desc),
        'direct_valid': json.loads((out / 'direct-valid.json').read_text())['fifth_state'],
        'direct_invalid': json.loads((out / 'direct-invalid.json').read_text())['fifth_state'],
        'coupled': json.loads((out / 'coupled/native-coupled-gate.json').read_text())['gate'],
        'linux': json.loads((out / 'linux/native-linux-gate.json').read_text())['gate'],
        'physical_card_tested': False, 'safe_to_flash': False,
    }
    (out / 'offline-gate.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('native_offline_gate=PASS')


if __name__ == '__main__':
    main()
