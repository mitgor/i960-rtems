#!/usr/bin/env python3
"""Partition inclusive elapsed brackets; no claim of pure CPU time."""
import argparse,json,statistics,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('captures',nargs='+',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
repo=here/'project' if (here/'project').is_dir() else here.parents[1]
sys.path.insert(0,str(repo/'rtems/residentnet'))
from presentation_profile import decode
result={};reference_counts=None
for out in a.captures:
 options=json.loads((out/'presentation-options.json').read_text());rows=[];counts_by_frame=[]
 for g in range(1,521):
  d=decode((out/f'play-0-{g}.bin').read_bytes(),g,options=options)
  if options.get('wall_profile'):
   r=d['wall_regions'];counts_by_frame.append(r['counts']);t=[x*1000/r['hz'] for x in r['ticks']]
   if 100<=g<=499:
    assert r['counts'][0]==1 and min(r['counts'])>0
    rows.append(dict(inclusive_ms=t,partition_ms=[t[0]-t[1],t[1]-t[2],t[2]-t[3],t[3]],counts=r['counts'],empty_bracket_us=r['clock_read_ticks']*1e6/r['hz']))
 if rows:
  if reference_counts is None:reference_counts=counts_by_frame
  else:assert counts_by_frame==reference_counts,(out,'region call-count divergence')
  result[out.name]=dict(frames=len(rows),regions=['traversal_culling','subsector_other','wall_setup','wall_loop'],partition_mean_ms=[statistics.mean(r['partition_ms'][i] for r in rows) for i in range(4)],inclusive_mean_ms=[statistics.mean(r['inclusive_ms'][i] for r in rows) for i in range(4)],mean_calls=[statistics.mean(r['counts'][i] for r in rows) for i in range(4)],empty_bracket_mean_us=statistics.mean(r['empty_bracket_us'] for r in rows))
print(json.dumps(result,indent=2))
