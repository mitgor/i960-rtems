#!/usr/bin/env python3
"""Recheck the accepted old/new cached N1 captures without touching hardware."""
import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'game/doom/runtime/cache_bench'))
from verify import NAMES, verify

OLD = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/tmp/i960-n1-accepted')
NEW = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('/tmp/i960-cache-map-accepted/case')

for filename in ('template.bin', 'relocations.bin', 'manifest.json'):
    old = (OLD / 'old-build/admission' / filename).read_bytes()
    new = (NEW / 'engine' / filename).read_bytes()
    assert old == new, f'admitted engine differs: {filename}'

old = []
for n in range(1, 121):
    row = verify((OLD / 'old-run' / f'play-0-{n}.bin').read_bytes())
    assert row['generation'] == n
    old.append(row)
new = []
for n in range(1, 33):
    row = verify((NEW / 'run/persist/live-frames' / f'frame-{n:04d}.bin').read_bytes())
    assert row['generation'] == n
    new.append(row)

assert {r['dcache_status'] for r in old} == {0x7221}
assert {tuple(r['logical_registers']) for r in old} == {
    ('0x0', '0xc0000002', '0xff000001', '0xbd7ff002', '0x48484000')}
assert {r['dcache_status'] for r in new} == {0x8221}
assert {tuple(r['logical_registers']) for r in new} == {
    ('0x0', '0xc0000002', '0xffc00001', '0xc0800002', '0xff800001')}
assert all(r['cache']['effective_cache_enabled'] and r['cache']['template_matches'] == 1
           for r in old + new)
assert {r['address'] for r in old} == {'0xc0a1db20'}
assert {r['address'] for r in new} == {'0xc0f7b850'}

cases = []
for k, name in enumerate(NAMES):
    old_ms = [r['ms'] for r in old[:32] if r['case'] == k]
    new_ms = [r['ms'] for r in new if r['case'] == k]
    assert len(old_ms) == len(new_ms) == 4
    om, nm = statistics.median(old_ms), statistics.median(new_ms)
    cases.append(dict(case=k, name=name, old_ms=old_ms, new_ms=new_ms,
                      old_median_ms=om, new_median_ms=nm, new_speedup=om / nm))

result = dict(
    admitted_engine_sha256={f: hashlib.sha256((NEW / 'engine' / f).read_bytes()).hexdigest()
                            for f in ('template.bin', 'relocations.bin', 'manifest.json')},
    old=dict(frames_verified=len(old), dcache_status=hex(old[0]['dcache_status']),
             allocation=old[0]['address'], cache=old[0]['cache'],
             logical_registers=old[0]['logical_registers']),
    new=dict(frames_verified=len(new), dcache_status=hex(new[0]['dcache_status']),
             allocation=new[0]['address'], cache=new[0]['cache'],
             logical_registers=new[0]['logical_registers']),
    comparison_window=[1, 32], cases=cases,
    limitations='Diagnostic wall times include scheduler and 10 ms clock granularity; not gameplay FPS.')
print(json.dumps(result, indent=2))
