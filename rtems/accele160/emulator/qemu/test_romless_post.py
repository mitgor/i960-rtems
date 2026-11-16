#!/usr/bin/env python3
"""Offline BIOS handoff probe with stock vs disabled Mylex option ROM."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time


ROM_OFFSET = 0x30000
ROM_SIZE = 0x7000
MARKER = b'ACCELE160_BOOT_SECTOR_REACHED\n'


def boot_sector():
    code = bytearray(b'\xba\x02\x04')  # mov dx, 0x402 (SeaBIOS debug port)
    for character in MARKER:
        code += bytes((0xb0, character, 0xee))  # mov al, imm8; out dx, al
    code += b'\xeb\xfe'  # park after the marker
    if len(code) > 510:
        raise AssertionError('boot-sector code exceeds 510 bytes')
    return bytes(code).ljust(510, b'\x00') + b'\x55\xaa'


def run(qemu, bios, rom, disk, directory, label, seconds):
    debug = directory / f'{label}-debug.log'
    trace = directory / f'{label}-trace.log'
    stderr = directory / f'{label}-stderr.log'
    command = [str(qemu), '-machine', 'pc,accel=tcg', '-m', '64',
               '-display', 'none', '-serial', 'none', '-monitor', 'none',
               '-no-reboot', '-boot', 'order=c', '-bios', str(bios),
               '-device', 'accele160-pci-bridge,addr=05.0,multifunction=on',
               '-device', f'accele160-probe,addr=05.1,romfile={rom}',
               '-drive', f'file={disk},format=raw,if=ide',
               '-chardev', f'file,id=romdebug,path={debug}',
               '-device', 'isa-debugcon,iobase=0x402,chardev=romdebug',
               '-d', 'in_asm,guest_errors', '-D', str(trace)]
    with stderr.open('w') as stream:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=stream)
        try:
            time.sleep(seconds)
        finally:
            if process.poll() is None:
                process.terminate()
            process.communicate(timeout=5)
    debug_data = debug.read_bytes() if debug.exists() else b''
    trace_data = trace.read_text(errors='replace') if trace.exists() else ''
    stderr_data = stderr.read_text(errors='replace')
    return {
        'qemu_exit_code': process.returncode,
        'boot_sector_reached': MARKER in debug_data,
        'mylex_mailbox_submitted': 'accele160 lp mailbox submitted ' in stderr_data,
        'mylex_bar_accesses_logged': sum(
            line.startswith(('accele160 bar0 R ', 'accele160 bar0 W '))
            for line in stderr_data.splitlines()),
        'boot_sector_trace_seen': '0x00007c00:' in trace_data,
        'debug_tail': debug_data[-160:].decode('ascii', errors='replace'),
        'stderr_tail': stderr_data.splitlines()[-8:],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qemu', required=True, type=Path)
    parser.add_argument('--bios', required=True, type=Path)
    parser.add_argument('--image', required=True, type=Path)
    parser.add_argument('--seconds', type=float, default=8)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    flash = args.image.read_bytes()
    if len(flash) != 0x100000:
        parser.error('expected a saved 1 MiB flash image')
    stock_rom = flash[ROM_OFFSET:ROM_OFFSET + ROM_SIZE]
    if (stock_rom[:2] != b'\x55\xaa' or
            stock_rom[2] * 512 != ROM_SIZE or sum(stock_rom) & 255):
        parser.error('saved image has no valid Mylex x86 option ROM')
    disabled_rom = bytearray(stock_rom)
    disabled_rom[0] = 0  # invalidate 55AA without changing PCI device identity
    with tempfile.TemporaryDirectory(prefix='accele160-romless-post-') as name:
        directory = Path(name)
        disk = directory / 'boot.img'
        disk.write_bytes(boot_sector())
        stock_file = directory / 'stock.rom'
        stock_file.write_bytes(stock_rom)
        disabled_file = directory / 'disabled.rom'
        disabled_file.write_bytes(disabled_rom)
        stock_result = run(args.qemu, args.bios, stock_file, disk,
                           directory, 'stock', args.seconds)
        disabled_result = run(args.qemu, args.bios, disabled_file, disk,
                              directory, 'disabled', args.seconds)
    result = {
        'source_image_sha256': hashlib.sha256(flash).hexdigest(),
        'stock_option_rom_sha256': hashlib.sha256(stock_rom).hexdigest(),
        'disabled_option_rom_sha256': hashlib.sha256(disabled_rom).hexdigest(),
        'disabled_change': 'flash offset 0x30000: 0x55 -> 0x00',
        'seconds_per_run': args.seconds,
        'stock': stock_result,
        'disabled': disabled_result,
    }
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    if stock_result['boot_sector_reached'] or not stock_result['mylex_bar_accesses_logged']:
        raise AssertionError('stock-ROM run did not reproduce the BIOS wait')
    if not disabled_result['boot_sector_reached']:
        raise AssertionError('disabled-ROM run did not reach boot sector')
    if disabled_result['mylex_bar_accesses_logged']:
        raise AssertionError('disabled-ROM run still touched the Mylex BAR')


if __name__ == '__main__':
    main()
