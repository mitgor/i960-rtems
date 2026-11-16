#!/usr/bin/env python3
"""Run a packed native image through the opt-in i960/QEMU Debian probe."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('emulator', 'image', 'qemu', 'bios', 'kernel', 'initrd',
                 'serial-output', 'emulator-output', 'qemu-stderr-output',
                 'rom-output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--seconds', type=float, default=65)
    p.add_argument('--memory-mb', type=int, default=512)
    p.add_argument('--health-dma1', action='store_true')
    p.add_argument('--pdev-dma1', action='store_true')
    p.add_argument('--mirror-followups', action='store_true')
    p.add_argument('--next-observe', action='store_true')
    p.add_argument('--next-mirror', action='store_true')
    args = p.parse_args()
    with tempfile.TemporaryDirectory(prefix='accele160-native-card-') as temp:
        bridge = Path(temp) / 'bridge.sock'
        command = [str(args.emulator.resolve()), str(args.image.resolve()),
                   '60000000', '--board-id=11', '--quiet-trace',
                   f'--bridge-socket={bridge}', '--explore-native-ring-dma1']
        if args.health_dma1:
            command.append('--explore-native-ring-health-dma1')
        if args.pdev_dma1:
            command.append('--explore-native-ring-pdev-dma1')
        args.emulator_output.parent.mkdir(parents=True, exist_ok=True)
        with args.emulator_output.open('w') as log:
            emulator = subprocess.Popen(command, stdout=log,
                                        stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 30
                while not bridge.exists():
                    if emulator.poll() is not None:
                        raise RuntimeError('native emulator exited before bridge')
                    if time.monotonic() > deadline:
                        raise TimeoutError('native bridge not ready')
                    time.sleep(0.05)
                rom = [sys.executable,
                       str(Path(__file__).with_name('run_pci_rom.py')),
                       str(args.image.resolve()), '--qemu', str(args.qemu.resolve()),
                       '--bridge-socket', str(bridge), '--seconds', str(args.seconds),
                       '--memory-mb', str(args.memory_mb), '--bios',
                       str(args.bios.resolve()), '--kernel', str(args.kernel.resolve()),
                       '--initrd', str(args.initrd.resolve()),
                       '--kernel-append', 'console=ttyS0 earlyprintk=serial nokaslr',
                       '--serial-output', str(args.serial_output.resolve()),
                       '--qemu-stderr-output', str(args.qemu_stderr_output.resolve()),
                       '--output', str(args.rom_output.resolve()),
                       '--explore-native-poll', '--explore-native-set-mbox',
                       '--explore-native-ring-observe',
                       '--explore-native-ring-mirror',
                       '--explore-native-followup-observe', '--trace-live-reply']
                if args.mirror_followups:
                    rom.append('--explore-native-followup-mirror')
                if args.next_observe:
                    if not args.mirror_followups:
                        p.error('--next-observe requires --mirror-followups')
                    rom.append('--explore-native-next-observe')
                if args.next_mirror:
                    if not args.next_observe:
                        p.error('--next-mirror requires --next-observe')
                    rom.append('--explore-native-next-mirror')
                result = subprocess.run(rom, capture_output=True, text=True,
                                        timeout=max(90, args.seconds + 40))
                if result.returncode:
                    raise RuntimeError(result.stderr[-3000:])
                parsed = json.loads(result.stdout)
                print(f'native=PASS image={parsed["image_sha256"]} '
                      f'ioctls={[item["ioctl"] for item in parsed["mailbox_requests"]]} '
                      f'rom_blocks={parsed["rom_block_count"]}')
            finally:
                emulator.terminate()
                try:
                    emulator.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    emulator.kill()
                    emulator.wait()


if __name__ == '__main__':
    main()
