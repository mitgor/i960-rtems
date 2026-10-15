#!/usr/bin/env python3
"""Matched 100-frame loading profiles; no trimmed intervals or upload conflation."""
import argparse,hashlib,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('captures',type=Path,nargs='+');p.add_argument('--native',type=Path,required=True);a=p.parse_args();results={};reference=None
for capture in a.captures:
 frames=[json.loads(x) for x in (capture/'play-frames.jsonl').read_text().splitlines()];assert len(frames)==100
 pixels=[]
 for g in range(1,53):
  b=(capture/f'play-0-{g}.bin').read_bytes();n=(a.native/f'frame-{g}.bin').read_bytes()
  assert b[64000:64768]==n[64000:64768]
  assert [i for i,(x,y) in enumerate(zip(b[:64000],n[:64000])) if x!=y]==[29260,29261,29580,29581]
  pixels.append(hashlib.sha256(b[:64768]).hexdigest())
 if reference is None:reference=pixels
 else:assert reference==pixels,'matched runs changed pixels or palettes'
 ram=[json.loads(x) for x in (capture/'ram-diagnostics.jsonl').read_text().splitlines()]
 assert all(r['words'][34]==146 and r['words'][36:38]==[0,0] for r in ram)
 results[capture.name]=dict(first_frame_seconds=frames[0]['engine_seconds'],engine_upload_seconds=frames[0]['seconds']-frames[0]['engine_seconds'],first_frame_requests=frames[0]['wad_requests'],total_requests=frames[-1]['wad_requests'],warm_restart_seconds=frames[67]['seconds']-frames[65]['seconds'],warm_restart_requests=frames[67]['wad_requests']-frames[65]['wad_requests'],restart_interval_frames=[66,68],full_audit_pairs=len(json.loads((capture/'snapshots.json').read_text())),pingpong_fps=29/(frames[49]['seconds']-frames[20]['seconds']),known_native_pixel_differences=[29260,29261,29580,29581],all_52_palettes_exact=True)
print(json.dumps(results,indent=2))
