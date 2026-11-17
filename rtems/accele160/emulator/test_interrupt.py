#!/usr/bin/env python3
"""Exercise timer entry, a nested ISR call, and exact IP resumption."""
import hashlib
from pathlib import Path
import re
import struct
import subprocess
import tempfile

ROOT = Path(__file__).parent
PROBE_SHA = '9e4de94bbe60d16784dcdf15774fc6c57e975294fad410fb038c7b3461a3af71'


def main():
    probe = (ROOT / 'interrupt_probe.bin').read_bytes()
    if len(probe) != 312 or hashlib.sha256(probe).hexdigest() != PROBE_SHA:
        raise ValueError('interrupt microprogram identity changed')
    image = bytearray(0x100000)
    image[0xf0000:0xf0000 + len(probe)] = probe
    entry, prcb, control, table = (0xfeff0000, 0xfeffdd20,
                                   0xfeffd8a0, 0xfeff0200)
    struct.pack_into('<III', image, 0xfff40, entry, prcb,
                     (-entry - prcb) & 0xffffffff)
    struct.pack_into('<I', image, prcb - 0xfef00000 + 4, control)
    struct.pack_into('<I', image, prcb - 0xfef00000 + 0x10, table)
    struct.pack_into('<I', image, prcb - 0xfef00000 + 0x1c, 0xc0002000)
    struct.pack_into('<I', image, control - 0xfef00000 + 0x18, 0x00080000)
    struct.pack_into('<I', image, control - 0xfef00000 + 0x1c, 0x00006000)
    struct.pack_into('<I', image, table - 0xfef00000 + 0x20c, 0xfeff0100)
    with tempfile.TemporaryDirectory(prefix='accele160-interrupt-') as directory:
        rom = Path(directory) / 'interrupt.rom'
        aperture = Path(directory) / 'aperture.bin'
        rom.write_bytes(image)
        run = subprocess.run(
            [str(ROOT / 'build/accele160-emu'), str(rom), '1000',
             '--quiet-trace', '--explore-timer-interrupt',
             f'--dump-aperture={aperture}'],
            text=True, capture_output=True, timeout=15)
        marker = struct.unpack_from('<I', aperture.read_bytes(), 0x1f00)[0]
    if (run.returncode != 1 or marker != 1 or not re.search(
            r'stop cycle=\d+ reason=self-loop ip=feff0038', run.stdout)):
        raise AssertionError(f'marker={marker} stdout={run.stdout} stderr={run.stderr}')
    print('timer_interrupt=PASS vector=82 handler=feff0100 '
          'nested_call=PASS return_ip=feff0038 marker=1')


if __name__ == '__main__':
    main()
