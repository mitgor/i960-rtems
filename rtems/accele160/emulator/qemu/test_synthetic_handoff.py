#!/usr/bin/env python3
"""Explore SeaBIOS handoff after a fabricated controller-info reply.

This does not validate the stock i960 firmware or a physical card.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

from test_romless_post import MARKER, boot_sector


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qemu', required=True, type=Path)
    parser.add_argument('--emulator', required=True, type=Path)
    parser.add_argument('--image', required=True, type=Path)
    parser.add_argument('--bios', required=True, type=Path)
    parser.add_argument('--seconds', type=float, default=8)
    parser.add_argument('--linux-iso', type=Path,
                        help='boot an ISO through the stock option ROM')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='a160-', dir='/tmp') as name:
        directory = Path(name)
        bridge = directory / 'bridge.sock'
        disk = directory / 'boot.img'
        if not args.linux_iso:
            disk.write_bytes(boot_sector())
        emu_log = directory / 'emu.log'
        qemu_log = directory / 'qemu.log'
        serial_log = directory / 'serial.log'
        vga_image = args.output.with_suffix('.vga.ppm') if args.output else directory / 'vga.ppm'
        result_file = directory / 'result.json'
        with emu_log.open('w') as log:
            emu = subprocess.Popen([
                str(args.emulator.resolve()), str(args.image.resolve()),
                '60000000', '--board-id=11', '--quiet-trace',
                f'--bridge-socket={bridge}'], stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 90
            while not bridge.exists():
                if emu.poll() is not None:
                    raise RuntimeError('i960 emulator exited before bridge-ready')
                if time.monotonic() > deadline:
                    raise TimeoutError('i960 emulator did not become bridge-ready')
                time.sleep(0.05)
            command = [sys.executable,
                       str(Path(__file__).with_name('run_pci_rom.py')),
                       str(args.image.resolve()), '--qemu', str(args.qemu.resolve()),
                       '--bios', str(args.bios.resolve()), '--seconds', str(args.seconds),
                       '--bridge-socket', str(bridge), '--step-on-ack',
                       '--explore-rom-ioctls',
                       '--qemu-stderr-output', str(qemu_log),
                       '--output', str(result_file)]
            if args.linux_iso:
                command += ['--boot-cdrom', str(args.linux_iso.resolve()),
                            '--memory-mb', '512', '--serial-output', str(serial_log),
                            '--vga-snapshot', str(vga_image)]
            else:
                command += ['--boot-disk', str(disk)]
            if args.output:
                command += ['--rom-trace-output',
                            str(args.output.with_suffix('.rom-trace.log'))]
            rom = subprocess.run(command, capture_output=True, text=True,
                                 timeout=max(120, args.seconds + 30))
            if rom.returncode:
                raise RuntimeError(rom.stderr[-4000:] + '\nQEMU:\n' +
                                   qemu_log.read_text(errors='replace')[-4000:])
            result = json.loads(result_file.read_text())
            result['boot_sector_reached'] = MARKER.decode() in result['debug_port_text']
            result['linux_iso_boot_attempted'] = bool(args.linux_iso)
            result['serial_output'] = (
                serial_log.read_text(errors='replace')[-4096:]
                if serial_log.exists() else '')
            result['linux_guest_login_reached'] = (
                'Welcome to Alpine Linux' in result['serial_output'] and
                'localhost login:' in result['serial_output']) if args.linux_iso else False
            result['synthetic_completion_exploratory'] = True
            result['mailbox_event_log'] = [line for line in
                qemu_log.read_text(errors='replace').splitlines()
                if line.startswith(('accele160 lp ', 'accele160 EXPLORE'))]
            result['emu_log_tail'] = emu_log.read_text(errors='replace').splitlines()[-20:]
            result['qemu_log_tail'] = qemu_log.read_text(errors='replace').splitlines()[-30:]
            if args.output:
                args.output.write_text(json.dumps(result, indent=2) + '\n')
                shutil.copy2(qemu_log, args.output.with_suffix('.qemu.log'))
                shutil.copy2(emu_log, args.output.with_suffix('.emu.log'))
                if serial_log.exists():
                    shutil.copy2(serial_log, args.output.with_suffix('.serial.log'))
            print(json.dumps(result, indent=2))
            if not result['synthetic_ctlr_info_completed']:
                raise AssertionError('synthetic completion was not posted')
            if not args.linux_iso and not result['boot_sector_reached']:
                raise AssertionError('SeaBIOS did not reach the test boot sector')
            if args.linux_iso and not result['linux_guest_login_reached']:
                raise AssertionError('Linux ISO did not reach the serial login prompt')
        finally:
            emu.terminate()
            emu.wait(timeout=5)


if __name__ == '__main__':
    main()
