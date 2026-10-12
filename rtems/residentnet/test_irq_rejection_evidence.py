#!/usr/bin/env python3
import argparse,json,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=Path(__file__).resolve().parent;results=[]
with tempfile.TemporaryDirectory() as d:
 t=Path(d)
 for name in ('snapshots.json','ram-diagnostics.jsonl'):(t/name).write_bytes((a.capture/name).read_bytes())
 subprocess.run(['python3',str(r/'verify_irq_rejection.py'),str(t),'--output',str(t/'baseline.json')],check=True,stdout=subprocess.DEVNULL)
 for case,index in [('magic',0),('owner',2),('active',3),('frame',5),('priority',6),('vector',8),('count',11)]:
  rows=[json.loads(s) for s in (a.capture/'ram-diagnostics.jsonl').read_text().splitlines()];changed=False
  for row in rows:
   w=row['words'];v=w[40:52]
   if not v[0]:continue
   changed=True
   if case=='frame':v[5]=0
   elif case=='priority':v[6]=(v[6]&~0x1f0000)|(31<<16)
   else:v[index]=0
   w[40:52]=v
  assert changed;(t/'ram-diagnostics.jsonl').write_text('\n'.join(json.dumps(x) for x in rows)+'\n')
  run=subprocess.run(['python3',str(r/'verify_irq_rejection.py'),str(t),'--output',str(t/'mutated.json')],capture_output=True);assert run.returncode!=0,case;results.append(dict(case=case,rejected=True))
a.output.write_text(json.dumps(results,indent=2)+'\n');print('PASS: seven first-rejection identity/stack/priority/vector evidence mutations rejected')
