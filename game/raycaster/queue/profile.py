#!/usr/bin/env python3
import argparse,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('captures',type=Path);a=p.parse_args();med=statistics.median;runs={}
for name in ['base1','queue1','queue2','base2']:
 rows=json.loads((a.captures/('live-'+name)/'phases.json').read_text());groups={}
 for label in ['render','steady-publish','steady-ack']:
  chosen=[r for r in rows if r['label']==label]
  if not chosen:continue
  keys=['upload_ns','arm_ns','execute_ns','verify_ns','audit_ns','kernel_ns','wall_ns','cpu_ns']
  if label!='render':keys+=['targeted_ns','full_audit_ns']
  groups[label]={k.replace('_ns','_ms'):med(r[k] for r in chosen)/1e6 for k in keys}
 if name.startswith('queue'):
  frames=[r for r in rows if r['label']=='steady-publish'];acks=[r for r in rows if r['label']=='steady-ack'];assert len(frames)==len(acks)==80
  groups['publish_plus_ack']={k.replace('_ns','_ms'):med(f[k]+ack[k] for f,ack in zip(frames,acks))/1e6 for k in ['kernel_ns','wall_ns','cpu_ns','execute_ns','targeted_ns','full_audit_ns']}
 runs[name]=groups
summary={}
for group,names in [('baseline',['base1','base2']),('queue',['queue1','queue2'])]:
 summary[group]={label:{key:med(runs[n][label][key] for n in names) for key in runs[names[0]][label]} for label in runs[names[0]]}
print(json.dumps(dict(runs=runs,median_of_session_medians=summary,ordinary_targeted_bytes=2*(64+5120),full_audit_bytes_each_request=2*524288,limits='All times include host/firmware overhead. Audits are retained; queue frame cost includes its separate ACK. No faster unaudited operating mode or asynchronous publication is tested.'),indent=2))
