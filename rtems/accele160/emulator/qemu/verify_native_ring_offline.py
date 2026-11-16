#!/usr/bin/env python3
"""Replay native first-ring reply and guarded guest mirror without hardware."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
PROBE = ROOT / 'artifacts/current/accele160-myrs-guest-20261116/probe.py'
DIRECT = ROOT / 'rtems/accele160/emulator/test_native_set_mem_mbox_gate.py'
MIRROR = ROOT / 'rtems/accele160/emulator/qemu/verify_native_ring_mirror.py'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(cmd, log):
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    log.write_text('command=' + ' '.join(map(str, cmd)) + '\n' +
                   result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f'{log.name} failed with exit {result.returncode}')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('emulator', 'qemu', 'observer-image', 'reply-image', 'stock',
                 'bios', 'kernel', 'initrd', 'sixth-request', 'ring-slot',
                 'stock-output', 'output-dir'):
        ap.add_argument('--' + name, type=Path, required=True)
    ap.add_argument('--seconds', type=float, default=65)
    args = ap.parse_args()
    out = args.output_dir.resolve()
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    stock, old, new = (args.stock.read_bytes(), args.observer_image.read_bytes(),
                       args.reply_image.read_bytes())
    if len(stock) != len(old) or len(old) != len(new) or len(new) != 0x100000:
        raise AssertionError('stock and candidates must be exact 1 MiB')
    if sha(stock) != '0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943':
        raise AssertionError('wrong second-spare stock base')
    changed = [i for i, (a, b) in enumerate(zip(stock, new)) if a != b]
    if not changed or any(not 0x40000 <= i < 0xc0000 for i in changed):
        raise AssertionError('reply image differs outside intended firmware region')
    if old[0xe0000:0xe0200] != new[0xe0000:0xe0200]:
        raise AssertionError('card-specific descriptor mismatch')
    for label, extra in (('direct-valid', []),
                         ('direct-invalid', ['--corrupt-ring-control'])):
        run([sys.executable, str(DIRECT), '--emulator', str(args.emulator.resolve()),
             '--image', str(args.reply_image.resolve()), '--sixth-request',
             str(args.sixth_request.resolve()), '--ring-slot',
             str(args.ring_slot.resolve()), '--ring-reply', '--output',
             str(out / (label + '.json'))] + extra, out / (label + '.log'))
    for label, image in (('negative', args.observer_image),
                         ('positive', args.reply_image)):
        run([sys.executable, str(PROBE), '--emulator', str(args.emulator.resolve()),
             '--qemu', str(args.qemu.resolve()), '--image', str(image.resolve()),
             '--bios', str(args.bios.resolve()), '--kernel',
             str(args.kernel.resolve()), '--initrd', str(args.initrd.resolve()),
             '--native-set-mbox', '--native-ring-observe', '--native-ring-dma1',
             '--native-ring-mirror', '--output-dir', str(out / label),
             '--seconds', str(args.seconds)], out / (label + '.log'))
    run([sys.executable, str(MIRROR), '--negative-run', str(out / 'negative'),
         '--positive-run', str(out / 'positive'), '--negative-image',
         str(args.observer_image.resolve()), '--positive-image',
         str(args.reply_image.resolve()), '--stock-output',
         str(args.stock_output.resolve()), '--output', str(out / 'mirror.json')],
        out / 'mirror.log')
    mirror = json.loads((out / 'mirror.json').read_text())
    if mirror.get('gate') != 'PASS':
        raise AssertionError('paired ring mirror did not pass')
    receipt = {'gate': 'PASS', 'stock_sha256': sha(stock),
               'observer_image_sha256': sha(old), 'reply_image_sha256': sha(new),
               'changed_bytes': len(changed), 'changed_min': min(changed),
               'changed_max': max(changed), 'mirror': mirror,
               'physical_card_tested': False, 'safe_to_flash': False}
    (out / 'offline-ring-gate.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('native_ring_offline=PASS')


if __name__ == '__main__':
    main()
