#!/usr/bin/env python3
"""Re-run bounded native SET_MEM_MBOX direct and paired guest gates."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
PROBE = ROOT / 'artifacts/current/accele160-myrs-guest-20261116/probe.py'
DIRECT = ROOT / 'rtems/accele160/emulator/test_native_set_mem_mbox_gate.py'
PAIR = ROOT / 'rtems/accele160/emulator/qemu/verify_native_set_mbox.py'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(cmd, log):
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    log.write_text('command=' + ' '.join(map(str, cmd)) + '\n' +
                   result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f'{log.name} failed with exit {result.returncode}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('emulator', 'qemu', 'old-image', 'new-image', 'stock',
                 'bios', 'kernel', 'initrd', 'sixth-request', 'output-dir'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=65)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    old, new, stock = (args.old_image.read_bytes(), args.new_image.read_bytes(),
                       args.stock.read_bytes())
    if len(old) != len(new) or len(new) != len(stock) or len(new) != 0x100000:
        raise AssertionError('all images must be exact 1 MiB')
    if sha(stock) != '0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943':
        raise AssertionError('stock base is not verified second spare')
    diff = [i for i, (a, b) in enumerate(zip(stock, new)) if a != b]
    if not diff or any(not 0x40000 <= i < 0xc0000 for i in diff):
        raise AssertionError('new image differs outside intended firmware region')
    if old[0xe0000:0xe0200] != new[0xe0000:0xe0200]:
        raise AssertionError('candidate descriptor differs from old image')
    for label, extra in (('direct-valid', []), ('direct-invalid', ['--corrupt-control'])):
        cmd = [sys.executable, str(DIRECT), '--emulator', str(args.emulator.resolve()),
               '--image', str(args.new_image.resolve()), '--sixth-request',
               str(args.sixth_request.resolve()), '--output',
               str(out / (label + '.json'))] + extra
        run(cmd, out / (label + '.log'))
    if json.loads((out / 'direct-valid.json').read_text())['sixth_state'] != 'completed':
        raise AssertionError('direct valid setup did not complete')
    if json.loads((out / 'direct-invalid.json').read_text())['sixth_state'] != 'rejected':
        raise AssertionError('direct malformed setup was not rejected')
    for label, image in (('old', args.old_image), ('new', args.new_image)):
        cmd = [sys.executable, str(PROBE), '--emulator', str(args.emulator.resolve()),
               '--qemu', str(args.qemu.resolve()), '--image', str(image.resolve()),
               '--bios', str(args.bios.resolve()), '--kernel', str(args.kernel.resolve()),
               '--initrd', str(args.initrd.resolve()), '--native-set-mbox',
               '--output-dir', str(out / label), '--seconds', str(args.seconds)]
        run(cmd, out / (label + '.log'))
    run([sys.executable, str(PAIR), '--old-run', str(out / 'old'),
         '--new-run', str(out / 'new'), '--old-image', str(args.old_image.resolve()),
         '--new-image', str(args.new_image.resolve()), '--output',
         str(out / 'pair.json')], out / 'pair.log')
    pair = json.loads((out / 'pair.json').read_text())
    receipt = {'gate': 'PASS', 'old_image_sha256': sha(old),
               'new_image_sha256': sha(new), 'stock_sha256': sha(stock),
               'changed_bytes': len(diff), 'changed_min': min(diff),
               'changed_max': max(diff), 'pair': pair,
               'physical_card_tested': False, 'safe_to_flash': False}
    (out / 'offline-setup-gate.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('native_setup_offline=PASS')


if __name__ == '__main__':
    main()
