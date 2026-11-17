#!/usr/bin/env python3
"""Exercise PCI identity and BAR0 read/write paths with QEMU's qtest API."""
import argparse
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qemu', required=True, type=Path)
    parser.add_argument('--aperture-file', type=Path)
    args = parser.parse_args()
    seed = args.aperture_file.read_bytes() if args.aperture_file else bytes(8192)
    if len(seed) != 8192:
        raise ValueError('aperture seed must be 8192 bytes')
    device = 'accele160-probe,addr=05.1'
    if args.aperture_file:
        device += f',aperture-file={args.aperture_file.resolve()}'
    process = subprocess.Popen(
        [str(args.qemu.resolve()), '-machine', 'pc', '-m', '64',
         '-display', 'none', '-nodefaults', '-accel', 'qtest',
         '-device', 'accele160-pci-bridge,addr=05.0,multifunction=on',
         '-device', device, '-qtest', 'stdio'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1)

    def command(line):
        process.stdin.write(line + '\n')
        process.stdin.flush()
        response = process.stdout.readline().strip()
        if not response.startswith('OK'):
            raise AssertionError(f'{line}: {response}')
        return int(response.split()[1], 0) if len(response.split()) > 1 else None

    try:
        # PCI bus 0, slot 5: bridge function 0 and RAID function 1.
        command('outl 0xcf8 0x80002800')
        assert command('inl 0xcfc') == 0x29628086
        command('outl 0xcf8 0x80002900')
        identity = command('inl 0xcfc')
        if identity != 0x00501069:
            raise AssertionError(f'PCI identity {identity:#x}')
        command('outl 0xcf8 0x80002910')
        command('outl 0xcfc 0xffffffff')
        bar_mask = command('inl 0xcfc')
        if bar_mask != 0xffffe008:
            raise AssertionError(f'BAR size/type mask {bar_mask:#x}')
        command('outl 0xcfc 0xf0000008')
        command('outl 0xcf8 0x80002904')
        command('outw 0xcfc 0x0002')
        bar_base = 0xf0000000
        initial = command(f'readl {bar_base:#x}')
        expected = int.from_bytes(seed[:4], 'little')
        if initial != expected:
            raise AssertionError(f'BAR start {initial:#x}, expected {expected:#x}')
        report = command(f'readl {bar_base + 0x1f00:#x}')
        expected_report = int.from_bytes(seed[0x1f00:0x1f04], 'little')
        if report != expected_report:
            raise AssertionError(f'BAR report {report:#x}, expected {expected_report:#x}')
        command(f'writel {bar_base + 0x1ffc:#x} 0x12345678')
        observed = command(f'readl {bar_base + 0x1ffc:#x}')
        if observed != 0x12345678:
            raise AssertionError(f'BAR readback {observed:#x}')
        print(f'pci_bar=PASS identity=1069:0050 size=8192 '
              f'report={report:08x} readback=12345678')
    finally:
        process.terminate()
        process.communicate(timeout=5)


if __name__ == '__main__':
    main()
