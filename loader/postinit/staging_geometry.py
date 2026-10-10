#!/usr/bin/env python3
"""Model the pinned 4.07-0-29 successful staging allocator; no device access."""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def model(enquiry):
    if len(enquiry) < 128 or enquiry[4:7] != bytes([4, 7, 29]):
        raise ValueError('requires complete matching-version Enquiry2')
    word = lambda off: struct.unpack_from('<I', enquiry, off)[0]
    sectors = struct.unpack_from('<H', enquiry, 0x68)[0]
    unit = sectors * 512
    cache, flash, memory = word(0x1c), word(0x20), word(0x18)
    if not unit or flash != 0x80000 or cache % unit:
        raise ValueError('unsupported allocation geometry')
    count = cache // unit
    # C001EABC takes floor(flash/unit)+1 blocks; C001EAC8 subtracts two more.
    reserve = flash // unit + 1
    index = count - reserve - 2
    if not 0 <= index < count <= 0xffff:
        raise ValueError('allocator index underflow or truncation')
    base = 0xc0140000 + index * unit
    if base + reserve * unit > 0xc0000000 + memory:
        raise ValueError('predicted allocation exceeds reported DRAM')
    return dict(enquiry_sha256=hashlib.sha256(enquiry).hexdigest(),
                allocation_unit=unit, pool_blocks=count, reserved_blocks=reserve,
                starting_block=index, predicted_staging_base=base,
                allocation_end_exclusive=base+reserve*unit,
                pointer_variable=0xc0112a70,
                pointer_read_offset=(0xc0112a70-base) & 0xffffffff,
                predicted_only=True, pointer_observed=False,
                conditions=['matching 512 KiB startup route',
                            'successful allocator return',
                            'geometry unchanged since allocation',
                            'no upstream offset rejection or DMA alias surprise'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('enquiry')
    a = p.parse_args()
    try:
        print(json.dumps(model(Path(a.enquiry).read_bytes()), indent=2))
    except (ValueError, OSError) as exc:
        p.error(str(exc))


if __name__ == '__main__':
    main()
