#!/usr/bin/env python3
"""Boot a Linux ISO past the real x86 option ROM with native i960 replies."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emulator', type=Path, required=True)
    parser.add_argument('--qemu', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--bios', type=Path, required=True)
    parser.add_argument('--linux-iso', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=110)
    parser.add_argument('--serial-probe', action='store_true',
                        help='log into guest and capture read-only PCI and driver state')
    args = parser.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    names = ('native-linux-emu.log', 'native-linux-qemu.log',
             'native-linux-rom.json', 'native-linux-serial.log',
             'native-linux-gate.json')
    if any((out / name).exists() for name in names):
        raise FileExistsError('output directory already contains gate files')
    with tempfile.TemporaryDirectory(prefix='accele160-native-linux-') as tmp:
        bridge = Path(tmp) / 'bridge.sock'
        with (out / 'native-linux-emu.log').open('w') as log:
            emulator = subprocess.Popen(
                [str(args.emulator.resolve()), str(args.image.resolve()),
                 '60000000', '--board-id=11', '--quiet-trace',
                 f'--bridge-socket={bridge}'],
                stdout=log, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 15
                while not bridge.exists():
                    if emulator.poll() is not None:
                        raise RuntimeError('i960 emulator exited before bridge')
                    if time.monotonic() > deadline:
                        raise TimeoutError('i960 bridge did not appear')
                    time.sleep(0.05)
                command = [
                    'python3', str(Path(__file__).with_name('run_pci_rom.py')),
                    str(args.image.resolve()), '--qemu', str(args.qemu.resolve()),
                    '--bios', str(args.bios.resolve()),
                    '--bridge-socket', str(bridge), '--explore-native-poll',
                    '--trace-live-reply', '--boot-cdrom',
                    str(args.linux_iso.resolve()), '--memory-mb', '512',
                    '--boot-enter-on-prompt', '--seconds', str(args.seconds),
                    '--output', str(out / 'native-linux-rom.json'),
                    '--serial-output', str(out / 'native-linux-serial.log'),
                    '--qemu-stderr-output', str(out / 'native-linux-qemu.log')]
                if args.serial_probe:
                    command.append('--serial-login-probe')
                result = subprocess.run(command, capture_output=True, text=True,
                                        timeout=args.seconds + 45)
                if result.returncode:
                    raise RuntimeError('QEMU ROM probe failed: ' +
                                       result.stderr[-2000:])
            finally:
                emulator.terminate()
                emulator.wait(timeout=5)
    rom = json.loads((out / 'native-linux-rom.json').read_text())
    qemu = (out / 'native-linux-qemu.log').read_text(errors='replace')
    serial = (out / 'native-linux-serial.log').read_text(errors='replace')
    requests = [entry['ioctl'] for entry in rom['mailbox_requests']]
    completions = [line for line in qemu.splitlines() if line.startswith(
        'accele160 EXPLORE native firmware completion ')]
    expected = [0x01, 0x11, 0x15, 0xd0, 0x2d]
    if not rom['option_rom_entry_executed'] or requests[:5] != expected:
        raise AssertionError(f'option ROM did not submit five requests: {requests}')
    if len(completions) != 5 or any(
            f'ioctl=0x{code:02x}' not in line or 'status=0x0000' not in line
            for code, line in zip(expected, completions)):
        raise AssertionError('native five-request completion sequence missing')
    if ('localhost login:' not in serial or
            'stock firmware completion' in qemu or
            'synthetic IOCTL completion' in qemu):
        raise AssertionError('guest login or native-only reply condition failed')
    if args.serial_probe and (not rom.get('serial_probe') or
                              rom['serial_probe']['commands_sent'] !=
                              rom['serial_probe']['commands_total'] or
                              not rom['serial_probe']['end_marker_seen']):
        raise AssertionError('guest serial probe did not finish')
    gate = {
        'gate': 'PASS', 'requests': requests,
        'image_sha256': hashlib.sha256(args.image.read_bytes()).hexdigest(),
        'linux_iso_sha256': hashlib.sha256(args.linux_iso.read_bytes()).hexdigest(),
        'serial_login': True, 'native_completions': completions,
        'serial_probe': rom.get('serial_probe'),
        'scope': 'exploratory i960 interpreter plus modified QEMU and SeaBIOS',
        'physical_card_tested': False, 'safe_to_flash': False,
    }
    (out / 'native-linux-gate.json').write_text(json.dumps(gate, indent=2) + '\n')
    print('native_linux_guest=PASS')


if __name__ == '__main__':
    main()
