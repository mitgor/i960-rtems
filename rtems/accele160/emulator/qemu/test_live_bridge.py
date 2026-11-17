#!/usr/bin/env python3
"""qtest a running i960 interpreter through PCI PIATVR and the odd BAR page."""
import argparse
from pathlib import Path
import subprocess
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qemu', required=True, type=Path)
    parser.add_argument('--emulator', required=True, type=Path)
    parser.add_argument('--image', required=True, type=Path)
    parser.add_argument('--cycles', type=int, required=True)
    parser.add_argument('--expected-report', required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='accele160-bridge-') as directory:
        socket = Path(directory) / 'i960.sock'
        emu = subprocess.Popen(
            [str(args.emulator.resolve()), str(args.image.resolve()),
             str(args.cycles), '--board-id=11', '--quiet-trace',
             f'--bridge-socket={socket}'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        qemu = None
        try:
            deadline = time.monotonic() + 90
            while not socket.exists():
                if emu.poll() is not None:
                    raise AssertionError(f'emulator exited: {emu.communicate()}')
                if time.monotonic() > deadline:
                    raise TimeoutError('emulator did not reach bridge-ready')
                time.sleep(0.05)
            qemu = subprocess.Popen(
                [str(args.qemu.resolve()), '-machine', 'pc', '-m', '64',
                 '-display', 'none', '-nodefaults', '-accel', 'qtest',
                 '-device', 'accele160-pci-bridge,addr=05.0,multifunction=on',
                 '-device', f'accele160-probe,addr=05.1,bridge-socket={socket}',
                 '-qtest', 'stdio'], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1)

            def command(line):
                qemu.stdin.write(line + '\n')
                qemu.stdin.flush()
                response = qemu.stdout.readline().strip()
                if not response.startswith('OK'):
                    raise AssertionError(f'{line}: {response}; qemu={qemu.poll()}')
                return int(response.split()[1], 0) if len(response.split()) > 1 else None

            command('outl 0xcf8 0x80002800')
            assert command('inl 0xcfc') == 0x29628086
            command('outl 0xcf8 0x80002900')
            assert command('inl 0xcfc') == 0x00501069
            command('outl 0xcf8 0x80002910')
            command('outl 0xcfc 0xf0000008')
            command('outl 0xcf8 0x80002904')
            command('outw 0xcfc 0x0002')
            command('outl 0xcf8 0x80002944')
            assert command('inl 0xcfc') == 0xc0000000
            bar = 0xf0000000
            report = command(f'readl {bar + 0x1f00:#x}')
            assert report == int(args.expected_report, 16), hex(report)
            # Write a scratch word outside the 0x1f00 native report and read
            # it back through a remap. The same controller address must alias.
            command(f'writel {bar + 0x1ef0:#x} 0x12345678')
            assert command(f'readl {bar + 0x1ef0:#x}') == 0x12345678
            command(f'writeb {bar + 0x1ef1:#x} 0xab')
            assert command(f'readb {bar + 0x1ef1:#x}') == 0xab
            assert command(f'readl {bar + 0x1ef0:#x}') == 0x1234ab78
            command('outl 0xcfc 0xc0001000')
            assert command('inl 0xcfc') == 0xc0001000
            # Remapping changes the controller address by one page.
            assert command(f'readl {bar + 0x1ef0:#x}') != 0x1234ab78
            command('outl 0xcfc 0xc0000000')
            assert command(f'readl {bar + 0x1ef0:#x}') == 0x1234ab78
            print(f'live_bridge=PASS report={report:08x} '
                  'piatvr=c0000000,c0001000,c0000000 alias=PASS')
        finally:
            if qemu is not None:
                qemu.terminate()
                qemu.communicate(timeout=5)
            emu.terminate()
            emu.communicate(timeout=5)


if __name__ == '__main__':
    main()
