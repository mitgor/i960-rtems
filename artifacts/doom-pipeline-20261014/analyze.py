#!/usr/bin/env python3
import json,statistics,sys
from pathlib import Path
w=Path(sys.argv[1]);live=w/'live'
r=json.loads((w/'pipeline-replay.json').read_text());frames=[json.loads(x) for x in (live/'play-frames.jsonl').read_text().splitlines()]
r['mean_transfer_seconds']={str(crc):statistics.mean(f['transfer_seconds'] for f in frames[4:] if f['crc']==crc) for crc in (True,False)}
r['full_audit_pairs']=len(json.loads((live/'snapshots.json').read_text()))
r['crc_off_improvement_percent']=100*(r['fps_speedup']-1)
r['prior_single_buffer_dma_fps']=1.376780510070597
r['versus_prior_percent']={k:100*(v/r['prior_single_buffer_dma_fps']-1) for k,v in r['fps'].items()}
r['prior_comparison_limit']='Earlier build used forward/release inputs; not an isolated attribution of buffering or binary transport.'
r['native_comparison']=[]
for i in range(1,53):
 a=(live/f'play-0-{i}.bin').read_bytes();b=(w/'native-52'/f'frame-{i}.bin').read_bytes();assert len(a)==len(b)==65536
 diff=[j for j,(x,y) in enumerate(zip(a,b)) if x!=y]
 r['native_comparison'].append(dict(frame=i,differing_pixels=sum(j<64000 for j in diff),palette_differences=sum(64000<=j<64768 for j in diff),padding_differences=sum(j>=64768 for j in diff)))
(w/'measurements.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='native_comparison'},indent=2))
