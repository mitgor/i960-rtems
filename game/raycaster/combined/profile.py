#!/usr/bin/env python3
import argparse,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('captures',type=Path);a=p.parse_args();med=statistics.median;runs={}
keys=['upload_ns','arm_ns','execute_ns','verify_ns','audit_ns','kernel_ns','wall_ns','cpu_ns','targeted_ns','full_audit_ns']
for name in ['separate1','combined1','combined2','separate2']:
 rows=json.loads((a.captures/('live-'+name)/'phases.json').read_text());groups={}
 for label in ['steady-publish','steady-ack','steady-combined']:
  chosen=[r for r in rows if r['label']==label]
  if chosen:
   assert len(chosen)==80
   groups[label]={k.replace('_ns','_ms'):med(r[k] for r in chosen)/1e6 for k in keys}
 if name.startswith('separate'):
  pubs=[r for r in rows if r['label']=='steady-publish'];acks=[r for r in rows if r['label']=='steady-ack']
  groups['frame']={k.replace('_ns','_ms'):med(p[k]+ack[k] for p,ack in zip(pubs,acks))/1e6 for k in keys}
 else:groups['frame']=groups['steady-combined']
 runs[name]=groups
summary={mode:{k:med(runs[mode+str(i)]['frame'][k] for i in (1,2)) for k in runs[mode+'1']['frame']} for mode in ['separate','combined']}
gain={k:100*(1-summary['combined'][k]/v) for k,v in summary['separate'].items()}
print(json.dumps(dict(runs=runs,median_frame_ms=summary,reduction_percent=gain,steady_frames_each_session=80,paired_full_audit_bytes_per_request=1048576,limits='Separate frame is ACK(previous)+PUBLISH(next), combined is one callback; both retain full audits on every request. Timing excludes post-Board.step archive compression/model work and is not browser FPS.'),indent=2))
