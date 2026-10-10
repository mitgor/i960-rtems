#!/usr/bin/env python3
"""Wrap the exact ROM-hook candidate in the matching offline Fujitsu MIMG.

This checks byte layout only. It neither talks to the controller nor validates
the updater's acceptance or the safety of its erase/program sequence.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from build_image import build

VENDOR_SHA = '660a81acfad40b65e3f45adca59227989652332eb854af2023adaa653c9c54a6'
START, END = 0x30000, 0x68000


def sha(data):
    return hashlib.sha256(data).hexdigest()


def package(stock, unpacked, hook, candidate, vendor):
    expected, image_report = build(stock, unpacked, hook)
    if candidate != expected:
        raise ValueError('candidate does not reproduce from pinned ROM-hook builder')
    if sha(vendor) != VENDOR_SHA:
        raise ValueError('requires exact archived Fujitsu 4.07-0-29 MIMG')
    if (vendor[:8] != b'MIMGMYLX' or vendor[13] != 2 or
            struct.unpack_from('<I', vendor, 8)[0] != len(vendor) - 10 or
            len(vendor[512:-10]) != END - START or
            vendor[512:-10] != stock[START:END]):
        raise ValueError('vendor component does not match installed stock region')
    result = vendor[:512] + candidate[START:END] + vendor[-10:]
    if stock[:START] + result[512:-10] + stock[END:] != candidate:
        raise ValueError('candidate changes outside the type-2 firmware component')
    report = dict(
        experimental=True, flash_ready=False, hardware_validated=False,
        vendor_acceptance_verified=False, recovery_verified=False,
        stock_sha256=sha(stock), candidate_sha256=sha(candidate),
        vendor_sha256=sha(vendor), package_sha256=sha(result),
        package_size=len(result), component_offset=START,
        component_length=END - START, header_and_trailer_unchanged=True,
        reconstructs_full_candidate=True, image_report=image_report,
        warning='Offline layout only; 2B/1 rewrites the lower 496 KiB and recovery is unverified.')
    return result, report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('stock', 'unpacked', 'hook', 'candidate', 'vendor', 'out'):
        p.add_argument('--' + name, required=True, type=Path)
    a = p.parse_args()
    manifest = a.out.with_suffix(a.out.suffix + '.json')
    if a.out.exists() or manifest.exists():
        p.error('output or manifest already exists')
    try:
        result, report = package(*(getattr(a, name).read_bytes() for name in
                                   ('stock', 'unpacked', 'hook', 'candidate', 'vendor')))
    except (OSError, ValueError) as e:
        p.error(str(e))
    with a.out.open('xb') as f:
        f.write(result)
    with manifest.open('x') as f:
        json.dump(report, f, indent=2)
        f.write('\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
