#!/usr/bin/env python3
import hashlib,json,statistics,sys
from pathlib import Path
w=Path(sys.argv[1]);live=w/'live';out={};frames=[json.loads(l) for l in (live/'play-frames.jsonl').read_text().splitlines()]
r=json.loads((w/'bulk-replay.json').read_text());blocks=r['blocks'];fps={op:10/sum(5/b['fps'] for b in blocks if b['method']==op) for op in (9,11)}
out.update(fps=fps,fps_speedup=fps[11]/fps[9],fps_improvement_percent=100*(fps[11]/fps[9]-1),mean_transfer_seconds=r['mean_transfer_seconds'],transfer_speedup=r['mean_transfer_seconds']['9']/r['mean_transfer_seconds']['11'],blocks=blocks,mean_png_seconds=statistics.mean(f['png_seconds'] for f in frames),paired_comparisons=r['paired_comparisons'],full_audit_pairs=len(json.loads((live/'snapshots.json').read_text())))
rows=[]
for i in range(1,29):
 card=(live/f'play-0-{i}.bin').read_bytes();host=(w/'native-28'/f'frame-{i}.bin').read_bytes();different=[j for j,(a,b) in enumerate(zip(card[:64000],host[:64000])) if a!=b]
 assert card[64000:]==host[64000:]
 rows.append(dict(frame=i,differing_pixels=len(different),bounds=[min(j%320 for j in different),min(j//320 for j in different),max(j%320 for j in different),max(j//320 for j in different)] if different else None))
out['native_comparison']=rows
(w/'measurements.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
