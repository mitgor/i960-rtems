#!/usr/bin/env python3
"""Rebase the accepted October RAM-admission flash patch onto this stock spare.

Build and audit only. Never accesses PCI or issues a flash command.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'host/accele160/helper'))
from audit_dispatch_rehearsal import analyze  # noqa: E402

OCTOBER_STOCK_SHA = '0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a'
CURRENT_STOCK_SHA = '0ca0f4b6dd08d2f71102c6dbb174dfd1b151bce53f943bc571f66a85c9d6e943'
OCTOBER_CANDIDATE_SHA = '1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
HANDLER_SHA = '8d8c79c3b8c206608ef7221000991c0d75eb101ce06581fedc2a74522648ad34'
SERIAL_OFFSETS = {918411, 918412, 918413, 918414}
LOADER_BASE, HOOK, CAVE = 0xC000A000, 0xC000C9CC, 0xC000E1D8
SIZE = 1048576


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(ok, why):
    if not ok:
        raise ValueError(why)


def build(october_stock, current_stock, october_candidate, handler):
    for name, data, want in (
            ('October stock', october_stock, OCTOBER_STOCK_SHA),
            ('current stock', current_stock, CURRENT_STOCK_SHA),
            ('October candidate', october_candidate, OCTOBER_CANDIDATE_SHA),
            ('October handler', handler, HANDLER_SHA)):
        need(sha(data) == want, f'{name} identity mismatch')
    need(all(len(x) == SIZE for x in
             (october_stock, current_stock, october_candidate)) and
         len(handler) == 4324, 'image/handler size mismatch')
    serial_diff = {i for i, (x, y) in
                   enumerate(zip(october_stock, current_stock)) if x != y}
    need(serial_diff == SERIAL_OFFSETS, 'stock images differ beyond serial')

    old = analyze(october_stock)
    current = analyze(current_stock)
    previous = analyze(october_candidate)
    # The historical analyzer's accepted_stock flag pins only the October
    # serial. This card's stock bytes are pinned above and structurally
    # checked here, so its flag is expected to be false.
    need(old['accepted_stock'] and not previous['accepted_stock'] and
         current['loader']['checksum_passed'] and
         current['trailer_checksum_passed'],
         'stock/October candidate structure')
    need(old['loader']['flash_offset'] == current['loader']['flash_offset'] and
         old['loader']['size'] == current['loader']['size'] == 0x6000 and
         old['trailer_offset'] == current['trailer_offset'] and
         old['runtime'] == current['runtime'] == previous['runtime'],
         'loader/runtime/trailer layout changed')
    base = current['loader']['flash_offset']
    site = base + HOOK - LOADER_BASE
    cave = base + CAVE - LOADER_BASE
    trailer = current['trailer_offset']
    need(current_stock[site:site + 4] == bytes.fromhex('0000000a') and
         october_candidate[site:site + 4] == bytes.fromhex('0c180008') and
         current_stock[cave:cave + len(handler)] == b'\xff' * len(handler) and
         october_candidate[cave:cave + len(handler)] == handler,
         'October hook/handler anchors changed')
    old_delta = {i for i, (x, y) in enumerate(zip(october_stock, october_candidate))
                 if x != y}
    allowed = (set(range(site, site + 4)) |
               set(range(cave, cave + len(handler))) |
               set(range(trailer + 24, trailer + 28)) |
               set(range(trailer + 124, trailer + 128)))
    need(old_delta <= allowed and {site, cave} <= old_delta,
         'October candidate changes outside audited loader/checksums')

    candidate = bytearray(current_stock)
    candidate[site:site + 4] = october_candidate[site:site + 4]
    candidate[cave:cave + len(handler)] = handler
    checksum = sum(struct.unpack_from('<%dI' % (0x6000 // 4), candidate, base)) & 0xffffffff
    struct.pack_into('<I', candidate, trailer + 24, checksum)
    trailer_checksum = sum(struct.unpack_from('<31I', candidate, trailer)) & 0xffffffff
    struct.pack_into('<I', candidate, trailer + 124, trailer_checksum)
    image = bytes(candidate)
    checked = analyze(image)
    changed = {i for i, (x, y) in enumerate(zip(current_stock, image)) if x != y}
    candidate_serial_diff = {i for i, (x, y) in
                             enumerate(zip(october_candidate, image)) if x != y}
    need(changed <= allowed and checked['runtime'] == current['runtime'] and
         checked['loader']['checksum_passed'] and
         checked['trailer_checksum_passed'] and
         image[0xf0000:] == current_stock[0xf0000:] and
         all(image[i] == current_stock[i] for i in SERIAL_OFFSETS) and
         candidate_serial_diff == SERIAL_OFFSETS,
         'current-spare candidate boundary/checksum audit failed')
    report = {
        'stock_sha256': CURRENT_STOCK_SHA,
        'candidate_sha256': sha(image),
        'october_candidate_sha256': OCTOBER_CANDIDATE_SHA,
        'handler_sha256': HANDLER_SHA,
        'changed_bytes': len(changed),
        'loader_hook_offset': site,
        'handler_offset': cave,
        'loader_checksum': f'0x{checksum:08x}',
        'trailer_checksum': f'0x{trailer_checksum:08x}',
        'serial_preserved': True,
        'only_serial_diff_from_october_candidate': True,
        'runtime_unchanged': True,
        'boot_block_unchanged': True,
        'known_checksums_pass': True,
        'flash_command_issued': False,
    }
    return image, report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('october_stock', 'current_stock', 'october_candidate',
                 'handler', 'out'):
        p.add_argument('--' + name.replace('_', '-'), type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        raise FileExistsError(a.out)
    image, report = build(a.october_stock.read_bytes(),
                          a.current_stock.read_bytes(),
                          a.october_candidate.read_bytes(),
                          a.handler.read_bytes())
    a.out.mkdir(parents=True)
    (a.out / 'candidate.bin').write_bytes(image)
    (a.out / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
