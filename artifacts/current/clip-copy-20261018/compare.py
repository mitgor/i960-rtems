#!/usr/bin/env python3
"""Compare candidate card frames against exact accepted cached-map baseline."""
import argparse
import json
import statistics
import struct
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'artifacts/current/cache-map-20261018/plain.tar.xz'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate', type=Path, help='archive with case/ or extracted case directory')
a = p.parse_args()

def inspect(case):
    frames = [(case / 'run/persist/live-frames' / f'frame-{n:04d}.bin').read_bytes()
              for n in range(1, 33)]
    assert all(len(b) == 65536 for b in frames)
    records = [struct.unpack_from('<32I', b, 64768) for b in frames]
    assert all(r[:4] == (0x31524650, 1, n, 2) and
               r[16:20] == (0x31555043, 1, 1, 10)
               for n, r in enumerate(records, 1))
    page = (case / 'run/persist/quiescent-page.bin').read_bytes()
    ticks = struct.unpack_from('<32I', page, 0xe00)
    assert all(y > x for x, y in zip(ticks, ticks[1:]))
    return frames, records, ticks

def report(base, candidate):
    bf, br, bt = inspect(base)
    cf, cr, ct = inspect(candidate)
    assert all(b[:64768] == c[:64768] for b, c in zip(bf, cf)), 'Doom pixels/palette changed'
    selected = list(range(11, 31))
    phases = {'renderer': 4, 'bsp_walls': 5, 'planes': 6,
              'masked': 7, 'presentation_copy': 8}
    out = {'window': [12, 31], 'pixel_palette_exact': True,
           'phase_ms': {name: {'baseline_mean': statistics.mean(br[i][field] for i in selected),
                               'candidate_mean': statistics.mean(cr[i][field] for i in selected)}
                        for name, field in phases.items()},
           'card_fps': {'baseline': 1900 / (bt[30] - bt[11]),
                        'candidate': 1900 / (ct[30] - ct[11])}}
    out['card_fps']['percent_change'] = 100 * (out['card_fps']['candidate'] /
                                               out['card_fps']['baseline'] - 1)
    return out

with tempfile.TemporaryDirectory(prefix='i960-clip-compare-') as tmp:
    tmp = Path(tmp)
    with tarfile.open(BASE) as t:
        t.extractall(tmp / 'baseline', filter='data')
    if a.candidate.is_dir():
        candidate = a.candidate / 'case' if (a.candidate / 'case').exists() else a.candidate
    else:
        with tarfile.open(a.candidate) as t:
            t.extractall(tmp / 'candidate', filter='data')
        candidate = tmp / 'candidate/case'
    print(json.dumps(report(tmp / 'baseline/case', candidate), indent=2))
