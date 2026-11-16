#!/usr/bin/env python3
"""Make a pinned OFFLINE spare image with its x86 option ROM disabled."""
import argparse
import hashlib
import json
from pathlib import Path


ACCEPTED_CANDIDATE_SHAS = {
    '6f16d71310d75937b5f3961b1faae81eab3258a29371c8505d788c50c545e3bd': 'first-spare',
    '32f86984f52183c392ceca34995609ddd07d050851bd0e735a5aff8f72d77976': 'second-spare',
}
ROM_OFFSET = 0x30000
ROM_SIZE = 0x7000


def build(candidate):
    source_sha = hashlib.sha256(candidate).hexdigest()
    if len(candidate) != 0x100000 or source_sha not in ACCEPTED_CANDIDATE_SHAS:
        raise ValueError('input must be an exact saved spare native-ROM candidate')
    rom = candidate[ROM_OFFSET:ROM_OFFSET + ROM_SIZE]
    if rom[:2] != b'\x55\xaa' or rom[2] * 512 != ROM_SIZE or sum(rom) & 255:
        raise ValueError('unexpected stock x86 option-ROM header')
    output = bytearray(candidate)
    output[ROM_OFFSET] = 0
    output = bytes(output)
    changed = [i for i, (before, after) in enumerate(zip(candidate, output))
               if before != after]
    if changed != [ROM_OFFSET] or output[0x40000:] != candidate[0x40000:]:
        raise AssertionError('unexpected change outside x86 ROM header')
    receipt = {
        'source_sha256': source_sha,
        'source_card': ACCEPTED_CANDIDATE_SHAS[source_sha],
        'output_sha256': hashlib.sha256(output).hexdigest(),
        'changed_flash_offsets': ['0x30000'],
        'old_byte': '0x55', 'new_byte': '0x00',
        'i960_firmware_and_reset_block_unchanged': True,
        'physical_boot_tested': False,
        'safe_to_flash': False,
    }
    return output, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    output, receipt = build(args.candidate.read_bytes())
    args.output.write_bytes(output)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
