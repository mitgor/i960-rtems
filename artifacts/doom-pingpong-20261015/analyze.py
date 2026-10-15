#!/usr/bin/env python3
import argparse,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--native',type=Path,required=True);a=p.parse_args()
rows=[json.loads(x) for x in (a.capture/'play-frames.jsonl').read_text().splitlines()];assert len(rows) in (52,100)
assert sum(x['profile']['cpu_samples']['render'] for x in rows)>0
for g in range(1,53):
 b=(a.capture/f'play-0-{g}.bin').read_bytes();n=(a.native/f'frame-{g}.bin').read_bytes()
 assert b[64000:64768]==n[64000:64768]
 assert [i for i,(x,y) in enumerate(zip(b[:64000],n[:64000])) if x!=y]==[29260,29261,29580,29581],g
blocks=[]
for lo,hi,name in [(5,15,'host-dma'),(21,50,'pingpong')]:
 r=rows[lo-1:hi];elapsed=r[-1]['seconds']-r[0]['seconds'];sample=r[1:]
 blocks.append(dict(name=name,first=lo,last=hi,fps=(hi-lo)/elapsed,wall_ms={k:statistics.mean(x['profile'][k] for x in sample) for k in sample[0]['profile'] if k.endswith('_ms')},sampled_cpu_ms={k:statistics.mean(x['profile']['cpu_samples'][k]*10 for x in sample) for k in sample[0]['profile']['cpu_samples']},mean_transfer_ms=statistics.mean(x['transfer_seconds'] for x in sample)*1000,mean_readback_ms=statistics.mean(x['readback_seconds'] for x in sample)*1000,interval_min_ms=min((b['seconds']-a['seconds'])*1000 for a,b in zip(r,r[1:])),interval_max_ms=max((b['seconds']-a['seconds'])*1000 for a,b in zip(r,r[1:]))))
print(json.dumps(dict(blocks=blocks,known_native_pixel_differences=[29260,29261,29580,29581],all_palettes_exact=True,full_audit_pairs=len(json.loads((a.capture/'snapshots.json').read_text())),first_frame_seconds=rows[0]['engine_seconds'],wad_reads_before_activation=rows[15]['wad_requests'],wad_reads_after_activation=rows[-1]['wad_requests']-rows[15]['wad_requests']),indent=2))
