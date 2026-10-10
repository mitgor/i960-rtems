#!/usr/bin/env python3
"""Produce an exact, offline three-write staging plan for the ROM hook.

This only prepares bytes for a future RAM-staging rehearsal. It does not
contact the controller or issue an erase/program command.
"""
import argparse
import hashlib
import json
from pathlib import Path

STOCK_SHA = '43d661af9dee28f531dcce525f8997e5fd11fc879d4a4e8bb07c5ac54a872a93'
CANDIDATE_SHA = 'a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0'
PATCHES = ((0x60000, 48, 'hook'),
           (0x67f68, 4, 'metadata-entry'),
           (0x67fdc, 4, 'metadata-checksum'))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build_plan(stock, candidate, hook):
    if len(stock) != 0x80000 or len(candidate) != 0x80000:
        raise ValueError('images must be 512 KiB')
    if sha(stock) != STOCK_SHA or sha(candidate) != CANDIDATE_SHA:
        raise ValueError('requires exact pinned stock and ROM-hook candidate')
    if len(hook) != 48 or candidate[0x60000:0x60030] != hook:
        raise ValueError('target hook differs from candidate')
    rebuilt = bytearray(stock)
    entries = []
    for offset, count, name in PATCHES:
        before = stock[offset:offset+count]
        after = candidate[offset:offset+count]
        if before == after:
            raise ValueError('patch has no changed bytes: ' + name)
        rebuilt[offset:offset+count] = after
        entries.append(dict(name=name, offset=offset, length=count,
                            before_sha256=sha(before), after_sha256=sha(after),
                            before_hex=before.hex(), after_hex=after.hex()))
    if bytes(rebuilt) != candidate:
        raise ValueError('candidate changes outside three pinned staging writes')
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('stock', 'candidate', 'hook'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args()
    stock = args.stock.read_bytes()
    candidate = args.candidate.read_bytes()
    hook = args.hook.read_bytes()
    entries = build_plan(stock, candidate, hook)
    args.out_dir.mkdir(parents=True, exist_ok=False)
    for e in entries:
        start, count, name = e['offset'], e['length'], e['name']
        (args.out_dir/(name+'-before.bin')).write_bytes(stock[start:start+count])
        (args.out_dir/(name+'-after.bin')).write_bytes(candidate[start:start+count])
    report = dict(offline_only=True, no_hardware_access=True,
                  flash_ready=False, stock_sha256=STOCK_SHA,
                  candidate_sha256=CANDIDATE_SHA, patch_count=len(entries),
                  patch_bytes=sum(e['length'] for e in entries),
                  changed_bytes=sum(a != b for a,b in zip(stock,candidate)),
                  requires_live_full_staging_validation=True,
                  requires_verified_programming_and_fresh_flash_readback=True,
                  patches=entries)
    (args.out_dir/'stage-plan.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
