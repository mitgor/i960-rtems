#!/usr/bin/env python3
"""Replay two bounded AcceleRAID runs and their paired full-flash audits."""
import hashlib
import json
import struct
from pathlib import Path

root = Path(__file__).resolve().parent
oracle = (root.parent / 'accele160-doom-first-frame-20261017' /
          'native-requests.bin').read_bytes()
stock = '1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
reference_pixels = reference_palette = None
run_boots = []

for run in sorted(root.glob('accepted-*')):
    result = json.loads((run / 'result.json').read_text())
    run_boots.append(result['boot_id'])
    assert result['full_audits_before'] and result['firmware_sha256'] == stock
    assert result['card']['bdf'] == '0000:37:09.1'
    assert result['old']['driver'] is None
    for i in (0, 1):
        audit = run / f'pre-{i}'
        req = json.loads((audit / 'request.json').read_text())
        check = json.loads((audit / 'result.json').read_text())
        assert req['boot_id'] == result['boot_id']
        assert req['selector'] == 9 and req['length'] == 1048576
        assert check['bytes'] == 1048576 and check['sha256'] == stock
        assert check['old_after']['driver'] is None
        assert (audit / 'status.txt').read_text().strip() == (
            'done=1 status=0 residual=0 selector=9 length=1048576 '
            'released=0 guard_changes=0')
    build = root / 'accepted-0/build'  # both runs used one byte-identical image
    for name, key in (('kernel.bin', 'kernel_sha256'),
                      ('image.bin', 'image_sha256')):
        assert hashlib.sha256((build / name).read_bytes()).hexdigest() == result[key]
    reads = json.loads((run / 'persist/engine-reads.json').read_text())
    assert len(reads) == result['engine_wad_reads'] >= 5043
    for i, row in enumerate(reads):
        assert row['request_seq'] == 42 + i
        assert 0 < row['n'] <= 4096 and row['offset'] + row['n'] <= 28795076
        if i < 5043:
            assert (row['offset'], row['n']) == struct.unpack_from('<II', oracle, i * 8)
    frame = (run / 'persist/game-frame.bin').read_bytes()
    assert len(frame) == 65536
    assert hashlib.sha256(frame).hexdigest() == result['game_frame_sha256']
    assert (run / 'persist/game-frame.pgm').read_bytes() == (
        b'P5\n320 200\n255\n' + frame[:64000])
    pixels = hashlib.sha256(frame[:64000]).hexdigest()
    palette = hashlib.sha256(frame[64000:64768]).hexdigest()
    if reference_pixels is None:
        reference_pixels, reference_palette = pixels, palette
    else:
        assert (pixels, palette) == (reference_pixels, reference_palette)
    timing = result['frame_timing']
    ticks = struct.unpack_from('<32I', frame, 64768)
    assert timing['frames'] == 32 and timing['timer_hz'] == 100
    assert ticks[0] == timing['first_tick'] and ticks[-1] == timing['last_tick']
    assert list(ticks[i] - ticks[i-1] for i in range(1, 32)) == timing['interframe_ticks']
    assert abs(timing['render_fps'] - 3100 / (ticks[-1] - ticks[0])) < 1e-12
    page = (run / 'persist/quiescent-page.bin').read_bytes()
    assert len(page) == 4096
    trace = struct.unpack_from('<16I', page, 0xcc0)
    claim = struct.unpack_from('<16I', page, 0xb40)
    engine = struct.unpack_from('<16I', page, 0xc40)
    assert trace[0] == 0x31435254 and trace[14] == 0
    assert claim[5:7] == (0x45495551, 0)
    assert engine[0:2] == (0x314d5246, 2) and engine[5] == 32
    assert result['release'] == 'reboot-only' and result['grant_retained']
    print(run.name, len(reads), f"{timing['render_fps']:.3f} FPS",
          trace[15], 'counted nested IRQs: verified')
assert len(run_boots) == 2 and len(set(run_boots)) == 2
for i, run in enumerate(sorted(root.glob('accepted-*'))):
    next_run = sorted(root.glob('accepted-*'))[i + 1] if i + 1 < 2 else None
    post_boot = None
    for j in (0, 1):
        audit = run / f'post-{j}'
        req = json.loads((audit / 'request.json').read_text())
        check = json.loads((audit / 'result.json').read_text())
        assert req['boot_id'] != run_boots[i] and req['selector'] == 9
        assert req['length'] == 1048576
        assert check['bytes'] == 1048576 and check['sha256'] == stock
        assert check['old_after']['driver'] is None
        assert (audit / 'status.txt').read_text().strip() == (
            'done=1 status=0 residual=0 selector=9 length=1048576 '
            'released=0 guard_changes=0')
        if post_boot is None:
            post_boot = req['boot_id']
        else:
            assert req['boot_id'] == post_boot
    if next_run is not None:
        assert post_boot == run_boots[i + 1]
    print(run.name, 'paired post-reset full-flash reads: verified')
