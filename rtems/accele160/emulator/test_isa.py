#!/usr/bin/env python3
"""Run Jx comparison and modpc microprogram checks in a synthetic reset ROM."""
import hashlib
from pathlib import Path
import re
import struct
import subprocess
import tempfile

ROOT = Path(__file__).parent
PROBE_SHA = 'd6dce3cda667694d183cc1588b444a91e7dabc34bd56cdb1727277aa5d24e87c'
ENTRY = 0xfeff0000
PRCB = 0xfeffdd20


def main():
    probe = (ROOT / 'isa_probe.bin').read_bytes()
    if hashlib.sha256(probe).hexdigest() != PROBE_SHA or len(probe) != 224:
        raise ValueError('microprogram identity changed')
    image = bytearray(0x100000)
    image[0xf0000:0xf0000 + len(probe)] = probe
    struct.pack_into('<III', image, 0xfff30 + 16, ENTRY, PRCB,
                     (-ENTRY - PRCB) & 0xffffffff)
    with tempfile.TemporaryDirectory() as directory:
        rom = Path(directory) / 'isa.rom'
        rom.write_bytes(image)
        run = subprocess.run([str(ROOT / 'build/accele160-emu'), str(rom),
                              '1000', '--strict', '--quiet-trace'],
                             text=True, capture_output=True, timeout=10)
    if (run.returncode != 1 or not re.search(
            r'stop cycle=\d+ reason=self-loop ip=feff00d8', run.stdout)):
        raise AssertionError(run.stdout + run.stderr)
    print('isa_probe=PASS chkbit cmpis cmpos cmpib cmpob scanbit spanbit modpc')


if __name__ == '__main__':
    main()
