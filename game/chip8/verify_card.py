#!/usr/bin/env python3
"""Offline native replay and existing RIO restoration validation of card captures."""
import argparse
import gzip
import hashlib
import json
import struct
import sys
from pathlib import Path
from host import HERE, Native, decode

sys.path.insert(0, str(HERE.parents[1] / 'rtems/transport'))
from run import verify_close
import wire

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('capture', type=Path)
p.add_argument('--payload', type=Path, required=True)
p.add_argument('--module', type=Path, required=True)
p.add_argument('--browser', action='store_true', help='browser trace without scripted validation.json')
a = p.parse_args()
code = a.payload.read_bytes()
meta = json.loads((a.capture / 'request.json').read_text())
assert hashlib.sha256(code).hexdigest() == meta['payload_sha256']
assert hashlib.sha256(a.module.read_bytes()).hexdigest() == meta['module_sha256']
image = wire.prepare(code)
assert hashlib.sha256(image).hexdigest() == meta['image_sha256']
verify_close(a.capture / 'close')
original = (a.capture / 'open/stage-before-a5.bin').read_bytes()
summary = json.loads((a.capture / 'summary.json').read_text())
assert summary['restored'] and summary['unloaded'] and not summary['driver_bound']
raw = gzip.decompress((a.capture / 'trace.bin.gz').read_bytes())
oracle, pos, sequence, audits, timings = Native(), 0, 0, 0, []
resets = keyed = full_audits = 0
while pos < len(raw):
    elapsed, n = struct.unpack_from('<QI', raw, pos)
    pos += 12
    incoming = raw[pos:pos+n]
    pos += n
    n, = struct.unpack_from('<I', raw, pos)
    pos += 4
    outgoing = raw[pos:pos+n]
    pos += n
    sequence += 1
    words = struct.unpack_from('<6I', incoming)
    resets += words[1] == 0
    keyed += words[3] != 0
    assert oracle.step(incoming) == outgoing, sequence
    assert decode(outgoing)['status'] == 0
    audit = a.capture / f'audit-{sequence:06d}.bin.gz'
    if audit.exists():
        after = gzip.decompress(audit.read_bytes())
        expected_size = 524288 if sequence % 32 == 0 else wire.bio.IMAGE_SIZE
        assert len(after) == expected_size
        full_audits += len(after) == 524288
        before = image[:wire.bio.OFFSET] + wire.block(incoming, sequence) + original[wire.bio.IMAGE_SIZE:]
        assert wire.response(before, after + original[len(after):]) == (0, outgoing)
        audits += 1
    elif sequence == 1 or sequence % 32 == 0:
        raise AssertionError(f'missing required audit {sequence}')
    timings.append(elapsed / 1e6)
assert pos == len(raw) and sequence == summary['steps']
if not a.browser:
    result = json.loads((a.capture / 'chip8-validation.json').read_text())
    assert result['matched_frames'] + 1 == sequence and result['matched_reset']
else:
    assert resets >= 2 and keyed > 0, 'browser must exercise key input and restart'
print(json.dumps(dict(verified_replies=sequence, verified_audit_snapshots=audits, verified_full_allocation_audits=full_audits,
                     resets=resets, keyed_requests=keyed,
                     restored=True, unloaded=True,
                     median_ms=sorted(timings)[len(timings)//2],
                     max_ms=max(timings)), indent=2))
