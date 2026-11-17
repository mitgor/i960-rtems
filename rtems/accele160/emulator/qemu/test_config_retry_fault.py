#!/usr/bin/env python3
"""Check that an invalid RTEMS payload does not keep the modeled host in retry.

This mutates only a temporary copy of a release candidate. It does not produce
an image for programming or access a physical card.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
from types import SimpleNamespace

from test_config_retry_post import run

PAYLOAD = 0x47000
STAGE2_STATUS = 0x1f04


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True, type=Path)
    parser.add_argument('--emulator', required=True, type=Path)
    parser.add_argument('--qemu', required=True, type=Path)
    parser.add_argument('--bios', required=True, type=Path)
    parser.add_argument('--qemu-data', type=Path)
    parser.add_argument('--seconds', type=float, default=45)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists')
    original = args.image.read_bytes()
    if len(original) != 0x100000 or original[PAYLOAD:PAYLOAD + 4] != b'RNT1':
        parser.error('input is not a packed 1 MiB native RTEMS image')
    with tempfile.TemporaryDirectory(prefix='a160-retry-fault-') as name:
        directory = Path(name)
        image = bytearray(original)
        image[PAYLOAD + 8] ^= 1  # change stored FNV, leaving the payload intact
        fault_image = directory / 'corrupt-payload.bin'
        fault_image.write_bytes(image)
        aperture = directory / 'aperture.bin'
        direct = subprocess.run(
            [str(args.emulator), str(fault_image), '4000000', '--board-id=11',
             '--quiet-trace', '--model-config-retry',
             f'--dump-aperture={aperture}'],
            text=True, capture_output=True, timeout=30, check=True)
        status = struct.unpack_from('<I', aperture.read_bytes(), STAGE2_STATUS)[0]
        release = [line for line in direct.stdout.splitlines()
                   if line.startswith('checkpoint config-retry released ')]
        settings = SimpleNamespace(
            emulator=args.emulator, qemu=args.qemu, bios=args.bios,
            qemu_data=args.qemu_data, seconds=args.seconds, retry_limit=120,
            retry_strap_low=False)
        host = run(settings, fault_image, directory, 'fault')
    ok = (status == 0x1003 and len(release) == 1 and
          host['boot_sector_reached'] and host['retry_released_seen_by_host'] and
          not host['host_stalled'] and host['host_config_accesses_logged'] > 0)
    receipt = {
        'gate': 'invalid native payload after early PCI release',
        'result': 'PASS' if ok else 'FAIL',
        'base_image_sha256': hashlib.sha256(original).hexdigest(),
        'temporary_fault_image_sha256': hashlib.sha256(image).hexdigest(),
        'mutation': 'flip bit 0 of stored payload FNV at flash offset 0x47008',
        'stage2_status': f'0x{status:04x}',
        'i960_release_lines': release,
        'host': host,
        'physical_boot_tested': False,
        'safe_to_flash': False,
    }
    args.output.write_text(json.dumps(receipt, indent=1) + '\n')
    print(f"config_retry_fault={receipt['result']} stage2={receipt['stage2_status']} "
          f"host_boot={int(host['boot_sector_reached'])}")
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
