#!/usr/bin/env python3
"""Offline MIMG packaging experiment; does not execute a flasher or access hardware."""
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


def package(stock, candidate, code, unpacked, vendor):
    expected, image_report = build(stock, code, unpacked)
    if candidate != expected:
        raise ValueError('candidate does not reproduce from current builder and supplied code')
    if sha(vendor) != VENDOR_SHA:
        raise ValueError('requires exact archived Fujitsu 4.07-0-29 MIMG')
    if (vendor[:8] != b'MIMGMYLX' or vendor[13] != 2 or
            struct.unpack_from('<I', vendor, 8)[0] != len(vendor)-10 or
            vendor[512:-10] != stock[START:END]):
        raise ValueError('vendor component does not match installed stock region')
    result = vendor[:512] + candidate[START:END] + vendor[-10:]
    reconstructed = stock[:START] + result[512:-10] + stock[END:]
    if reconstructed != candidate:
        raise ValueError('candidate contains changes outside firmware component')
    report = dict(experimental=True, flash_ready=False, vendor_acceptance_verified=False,
                  hardware_validated=False, package_sha256=sha(result),
                  vendor_sha256=sha(vendor), candidate_sha256=sha(candidate),
                  stock_sha256=sha(stock), size=len(result),
                  component_offset=START, component_length=END-START,
                  header_and_trailer_unchanged=True, reconstructs_full_candidate=True,
                  image_report=image_report,
                  warning='MIMG layout checked only. Programming erases broader regions; recovery is unproven.')
    return result, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('stock', 'candidate', 'code', 'unpacked', 'vendor', 'out'):
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args()
    out = Path(args.out)
    manifest = out.with_suffix(out.suffix+'.json')
    if out.exists() or manifest.exists():
        parser.error('output or manifest already exists')
    try:
        result, report = package(*(Path(getattr(args, n)).read_bytes()
                                  for n in ('stock', 'candidate', 'code', 'unpacked', 'vendor')))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    with out.open('xb') as f:
        f.write(result)
    with manifest.open('x') as f:
        json.dump(report, f, indent=2)
        f.write('\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
