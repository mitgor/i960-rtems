#!/usr/bin/env python3
"""Compare accepted stock/cached Doom phase trailers in frames 12–31."""
import hashlib
import json
import statistics
import struct
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCES = {
    'stock': ROOT / 'artifacts/current/accele160-doom-dma-20261017/hash-off.tar.gz',
    'cached': ROOT / 'artifacts/current/cache-map-20261018/plain.tar.xz',
}
with tempfile.TemporaryDirectory(prefix='i960-clip-phase-') as temp:
    roots = {}
    for label, archive in SOURCES.items():
        dest = Path(temp) / label
        dest.mkdir()
        with tarfile.open(archive) as t:
            t.extractall(dest, filter='data')
        roots[label] = dest / 'case'
    for filename in ('template.bin', 'relocations.bin', 'manifest.json'):
        payloads = [(root / 'engine' / filename).read_bytes() for root in roots.values()]
        assert payloads[0] == payloads[1], filename
    out = {'window': [12, 31], 'identical_admitted_engine': True, 'phases': {}}
    labels = {4: 'renderer', 5: 'bsp_and_walls', 6: 'planes',
              7: 'masked', 8: 'presentation_copy'}
    for label, root in roots.items():
        frames = [(root / 'run/persist/live-frames' / f'frame-{n:04d}.bin').read_bytes()
                  for n in range(12, 32)]
        assert all(len(frame) == 65536 for frame in frames)
        records = [struct.unpack_from('<32I', frame, 64768) for frame in frames]
        assert all(r[:4] == (0x31524650, 1, n, 2) and r[16:20] ==
                   (0x31555043, 1, 1, 10)
                   for n, r in zip(range(12, 32), records))
        out['phases'][label] = {
            name: dict(samples_ms=[r[index] for r in records],
                       mean_ms=statistics.mean(r[index] for r in records))
            for index, name in labels.items()}
        out['phases'][label]['pixel_palette_sha256'] = [
            hashlib.sha256(frame[:64768]).hexdigest() for frame in frames]
    assert out['phases']['stock']['pixel_palette_sha256'] == \
           out['phases']['cached']['pixel_palette_sha256']
    print(json.dumps(out, indent=2))
