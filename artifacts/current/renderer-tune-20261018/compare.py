#!/usr/bin/env python3
"""Compare exact new-card Doom frames over the fixed 12–31 steady window."""
import argparse
import json
import statistics
import struct
import tarfile
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('baseline', type=Path)
p.add_argument('candidate', type=Path)
a = p.parse_args()


def load(path):
    with tarfile.open(path) as archive:
        def member(name):
            return archive.extractfile('case/' + name).read()

        frames = [member(f'run/persist/live-frames/frame-{g:04d}.bin')
                  for g in range(1, 33)]
        page = member('run/persist/quiescent-page.bin')
        manifest = json.loads(member('engine/manifest.json'))
        assert all(len(frame) == 65536 for frame in frames)
        times = list(struct.unpack_from('<32I', page, 0xe00))
        assert all(y > x for x, y in zip(times, times[1:]))
        return frames, times, manifest


base, bt, bm = load(a.baseline)
new, nt, nm = load(a.candidate)
assert all(b[:64768] == n[:64768] for b, n in zip(base, new)), \
    'pixel or palette mismatch'
window = range(11, 31)
fields = {'renderer': 4, 'bsp_and_walls': 5, 'planes': 6,
          'masked': 7, 'presentation_copy': 8}
phases = {}
for name, index in fields.items():
    phases[name] = {
        'baseline_ms': statistics.mean(struct.unpack_from('<16I', base[i], 64768)[index]
                                       for i in window),
        'candidate_ms': statistics.mean(struct.unpack_from('<16I', new[i], 64768)[index]
                                        for i in window),
    }
bfps = 1900 / (bt[30] - bt[11])
nfps = 1900 / (nt[30] - nt[11])
report = {
    'frames': 32, 'steady_window': [12, 31], 'pixels_palette_exact': True,
    'baseline_fast_walls': bm.get('fast_walls'),
    'candidate_fast_walls': nm.get('fast_walls'),
    'baseline_wall_profile': bm.get('wall_profile'),
    'candidate_wall_profile': nm.get('wall_profile'),
    'baseline_fps': bfps, 'candidate_fps': nfps,
    'fps_change_percent': 100 * (nfps / bfps - 1), 'phase_ms': phases,
}
if nm.get('wall_profile'):
    ticks = [struct.unpack_from('<16I', new[i], 65024) for i in window]
    assert all(row[:5] == (0x314c4157, 1, i + 1, 4, 4166700) and row[6] == 0
               for i, row in zip(window, ticks))
    means = [statistics.mean(row[9 + 2 * region] * 1000 / row[4]
                             for row in ticks) for region in range(4)]
    report['wall_region_ms'] = {
        'bsp_root': means[0], 'traversal': means[0] - means[1],
        'subsector_other': means[1] - means[2],
        'wall_setup': means[2] - means[3], 'inner_wall_loop': means[3],
    }
print(json.dumps(report, indent=2))
