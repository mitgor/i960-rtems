#!/usr/bin/env python3
import argparse,json,statistics,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--native',type=Path,required=True);a=p.parse_args()
rows=[json.loads(x) for x in (a.capture/'play-frames.jsonl').read_text().splitlines()];assert len(rows)==52
assert sum(x['profile']['cpu_samples']['render'] for x in rows)>0, 'physical CPU sampler never advanced'
blocks=[];diffs=[]
for g,row in enumerate(rows,1):
 assert row['profile']['column_cases']==96 and row['profile']['column_mode']==(1 if 17<=g<=28 else 2 if 29<=g<=40 else 0)
 b=(a.capture/f'play-0-{g}.bin').read_bytes();n=(a.native/f'frame-{g}.bin').read_bytes();assert len(b)==len(n)==65536 and b[64000:64768]==n[64000:64768]
 positions=[i for i,(x,y) in enumerate(zip(b[:64000],n[:64000])) if x!=y]
 assert positions==[29260,29261,29580,29581], (g,positions)
 diffs.append(dict(frame=g,detail=row['profile']['detail'],count=len(positions),pixels=[dict(x=i%320,y=i//320,card=b[i],native=n[i]) for i in positions]))
for lo,hi,name in [(5,16,'baseline-before'),(17,28,'optimized-C'),(29,40,'i960-assembly'),(41,52,'baseline-after')]:
 r=rows[lo-1:hi];elapsed=r[-1]['seconds']-r[0]['seconds'];sample=r[1:] # omit first-frame setup from phase averages too
 wall={k:statistics.mean(x['profile'][k] for x in sample) for k in sample[0]['profile'] if k.endswith('_ms')}
 cpu={k:statistics.mean(x['profile']['cpu_samples'][k]*10 for x in sample) for k in sample[0]['profile']['cpu_samples']}
 blocks.append(dict(name=name,first=lo,last=hi,fps=11/elapsed,interval_ms=elapsed*1000/11,wall_ms=wall,sampled_cpu_ms=cpu,renderer_cpu_share=cpu['render']/wall['render_ms'],renderer_nonsampled_ms=wall['render_ms']-cpu['render'],profile_read_ms=statistics.mean(x['profile_read_seconds'] for x in sample)*1000))
baseline=22/sum(11/blocks[i]['fps'] for i in (0,3))
comparisons={b['name']:dict(fps=b['fps'],speedup=b['fps']/baseline,improvement_percent=100*(b['fps']/baseline-1)) for b in blocks[1:3]}
print(json.dumps(dict(blocks=blocks,baseline_fps=baseline,comparisons=comparisons,pixel_differences=diffs,full_audit_pairs=len(json.loads((a.capture/'snapshots.json').read_text())),sample_period_ms=10,cpu_measurement='timer-sampled task attribution, includes sampling error/IRQ attribution; not cycle-exact'),indent=2))
