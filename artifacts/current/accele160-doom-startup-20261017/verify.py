#!/usr/bin/env python3
"""Replay four bounded startup-stall captures against the pinned native oracle."""
import json
import struct
from pathlib import Path

root = Path(__file__).resolve().parent
oracle = (root.parent / 'accele160-doom-first-frame-20261017' /
          'native-requests.bin').read_bytes()
assert len(oracle) == 5043 * 8

for name in ('.', 'fixed-attempt0', 'idle-attempt0', 'unknown-attempt0'):
    path = root / name
    reads = json.loads((path / 'engine-reads.json').read_text())
    assert len(reads) == 1401, (name, len(reads))
    for i, row in enumerate(reads):
        assert (row['offset'], row['n']) == struct.unpack_from('<II', oracle, i * 8), (name, i)
        assert row['request_seq'] == 42 + i, (name, i)
    page_name = 'engine-stall-page.bin' if name == '.' else 'engine-fault-page.bin'
    page = (path / page_name).read_bytes()
    assert len(page) == 4096
    trace = struct.unpack_from('<16I', page, 0xcc0)
    report = struct.unpack_from('<16I', page, 0xc40)
    assert trace[0] == 0x31435254 and trace[14] == 0x40
    assert report[0:2] == (0x314d5246, 1) and report[14] >= 1401
    samples = json.loads((path / 'engine-trace.json').read_text())
    assert samples and any(int(s['words'][14], 16) == 0 for s in samples)
    if name == 'unknown-attempt0':
        bss = (path / 'engine-fault-bss-page.bin').read_bytes()
        assert len(bss) == 4096
        assert struct.unpack_from('<I', bss, 0x2d4)[0] == 1
        assert struct.unpack_from('<I', bss, 0x2b4)[0] == 0xc0714570
        assert struct.unpack_from('<4I', bss, 0x2e0) == (
            0xc075e440, 0xc075e5b0, 0xc075e720, 0xc075ea48)
    print(name, 'oracle prefix, owner fault and trace verified')
