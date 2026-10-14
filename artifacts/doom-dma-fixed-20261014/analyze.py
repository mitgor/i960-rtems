#!/usr/bin/env python3
"""Summarize closed A/B/B/A capture; preserve native/card differences explicitly."""
import hashlib,json,statistics,sys
from pathlib import Path
w=Path(sys.argv[1]);live=w/'live';r=json.loads((w/'dma-replay.json').read_text())
frames=[json.loads(l) for l in (live/'play-frames.jsonl').read_text().splitlines()]
out=dict(fps=r['fps'],fps_speedup=r['fps_speedup'],fps_improvement_percent=100*(r['fps_speedup']-1),mean_transfer_seconds=r['mean_transfer_seconds'],transfer_speedup=r['mean_transfer_seconds']['11']/r['mean_transfer_seconds']['12'],blocks=r['blocks'],mean_png_seconds=statistics.mean(f['png_seconds'] for f in frames),paired_comparisons=r['paired_seconds'],full_audit_pairs=len(json.loads((live/'snapshots.json').read_text())))
rows=[]
for i in range(1,29):
 card=(live/f'play-0-{i}.bin').read_bytes();host=(w/'native-28'/f'frame-{i}.bin').read_bytes()
 assert len(card)==len(host)==65536 and card[64000:]==host[64000:]
 different=[j for j,(a,b) in enumerate(zip(card[:64000],host[:64000])) if a!=b]
 rows.append(dict(frame=i,differing_pixels=len(different),bounds=[min(j%320 for j in different),min(j//320 for j in different),max(j%320 for j in different),max(j//320 for j in different)] if different else None))
out['native_comparison']=rows
if len(sys.argv)>2:
 old=Path(sys.argv[2]);out['previous_card_exact_frames']=[i for i in range(1,29) if (live/f'play-0-{i}.bin').read_bytes()==(old/f'play-0-{i}.bin').read_bytes()]
(w/'measurements.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
