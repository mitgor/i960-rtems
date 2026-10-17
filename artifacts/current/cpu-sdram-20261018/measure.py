#!/usr/bin/env python3
"""Replay physical i960 CPU-memory records and derive useful-byte rates."""
import argparse
import hashlib
import json
import statistics
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'game/doom/runtime/cache_bench'))
from verify import verify

N1 = ROOT / 'artifacts/current/cache-scaling-20261017/accepted.tar.xz'
N2 = ROOT / 'artifacts/current/cache-map-20261018/cache-bench.tar.xz'
EXPECTED_ARCHIVES = {
    'n1': '974df5742118518e9e3cab288413ef056cba708a4edd570ffd8ddc810bea7b34',
    'n2': '237f287c41549062603edbc4261e5f4c64375fcbc90c7a069f5b39fabb58461a',
}
MIB = 1024 * 1024
LOGICAL_BYTES = 4 * MIB

def frames(path, name, count):
    rows = []
    for n in range(1, count + 1):
        row = verify((path / name(n)).read_bytes())
        assert row['generation'] == n
        rows.append(row)
    return rows

def group(rows, kind):
    values = [r['ms'] for r in rows[:32] if r['case'] == kind]
    assert len(values) == 4
    median = statistics.median(values)
    return dict(samples_ms=values, median_ms=median,
                logical_mib=LOGICAL_BYTES / MIB,
                useful_mib_per_s=(LOGICAL_BYTES / MIB) * 1000 / median)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--n1', type=Path, default=N1)
    p.add_argument('--n2', type=Path, default=N2)
    a = p.parse_args()
    archive_hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest()
                      for name, path in (('n1', a.n1), ('n2', a.n2))}
    assert archive_hashes == EXPECTED_ARCHIVES, 'accepted archive identity'
    with tempfile.TemporaryDirectory(prefix='i960-cpu-sdram-') as temp:
        old_root, new_root = Path(temp) / 'n1', Path(temp) / 'n2'
        old_root.mkdir(); new_root.mkdir()
        with tarfile.open(a.n1) as archive:
            archive.extractall(old_root, filter='data')
        with tarfile.open(a.n2) as archive:
            archive.extractall(new_root, filter='data')
        old = frames(old_root / 'old-run', lambda n: f'play-0-{n}.bin', 120)
        stock = frames(old_root / 'new-v2-case/run/persist/live-frames',
                       lambda n: f'frame-{n:04d}.bin', 32)
        cached = frames(new_root / 'case/run/persist/live-frames',
                        lambda n: f'frame-{n:04d}.bin', 32)
        identities = {}
        for name in ('template.bin', 'relocations.bin', 'manifest.json'):
            sources = [old_root / 'old-build/admission' / name,
                       old_root / 'new-v2-case/engine' / name,
                       new_root / 'case/engine' / name]
            payloads = [f.read_bytes() for f in sources]
            assert payloads[0] == payloads[1] == payloads[2], name
            identities[name] = hashlib.sha256(payloads[0]).hexdigest()
        for name, rows, status, regs, enabled in (
            ('old', old, 0x7221,
             ('0x0', '0xc0000002', '0xff000001', '0xbd7ff002', '0x48484000'), True),
            ('new_stock', stock, 0x8221,
             ('0x0', '0xc0000002', '0xffc00001', '0xc0400002', '0xffe00001'), False),
            ('new_cached', cached, 0x8221,
             ('0x0', '0xc0000002', '0xffc00001', '0xc0800002', '0xff800001'), True)):
            assert all(r['dcache_status'] == status and
                       tuple(r['logical_registers']) == regs and
                       r['cache']['effective_cache_enabled'] == enabled
                       for r in rows), f'{name} cache state drift'
        cases = {}
        for kind, label in ((3, 'sequential_64k_read'),
                            (4, 'strided_64k_read'),
                            (5, 'sequential_64k_copy'),
                            (6, 'sequential_64k_clear')):
            cases[label] = {name: group(rows, kind) for name, rows in
                            (('old', old), ('new_stock', stock),
                             ('new_cached', cached))}
            if kind == 5:
                for value in cases[label].values():
                    value['aggregate_logical_mib_per_s'] = 2 * value['useful_mib_per_s']
        out = dict(source_archives={name: dict(sha256=digest)
                                    for name, digest in archive_hashes.items()},
                   admitted_engine_sha256=identities,
                   verified_frames=dict(old=len(old), new_stock=len(stock),
                                        new_cached=len(cached)),
                   window=[1, 32], cases=cases,
                   measurement='i960 timed volatile CPU loops; 10 ms RTEMS clock; '
                               'interrupts and loop overhead included; logical bytes, '
                               'not isolated SDRAM bus transactions or DMA bandwidth')
        print(json.dumps(out, indent=2))

if __name__ == '__main__':
    main()
