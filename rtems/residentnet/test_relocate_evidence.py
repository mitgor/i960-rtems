#!/usr/bin/env python3
"""Independent tampering checks for the closed relocated proof evidence."""
import argparse,copy,json,struct,tempfile
from pathlib import Path
from relocate_replay import prepare_relocated
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
events=[json.loads(x) for x in (a.capture/'upload-journal.jsonl').read_text().splitlines()];requests=[];responses=[];pending=None
for e in events:
 if 'errno' in e:continue
 req=bytes.fromhex(e['request']);op,n=struct.unpack_from('<I',req)[0],struct.unpack_from('<I',req,8)[0]
 if op==1:pending=req[32:32+n];requests.append(pending)
 elif op==2 and pending:
  w=list(struct.unpack_from('<16I',bytes.fromhex(e['response']),32))
  if not w[3] and w[1]==struct.unpack_from('<I',pending,4)[0]:responses.append(w);pending=None
assert len(requests)==len(responses) and not pending
prepare_relocated(a.capture,a.build,requests,responses)
results=[]
for case in ('template','manifest','return_value','missing_entry','base','summary_result','summary_base'):
 with tempfile.TemporaryDirectory() as tmp:
  t=Path(tmp)
  for name in ('relocate-results.json','relocate-template.bin'):(t/name).write_bytes((a.capture/name).read_bytes())
  if (a.capture/'cache-results.json').exists():(t/'cache-results.json').write_bytes((a.capture/'cache-results.json').read_bytes())
  if (a.capture/'owned-results.json').exists():(t/'owned-results.json').write_bytes((a.capture/'owned-results.json').read_bytes())
  if (a.capture/'engine-results.json').exists():(t/'engine-results.json').write_bytes((a.capture/'engine-results.json').read_bytes())
  prepare_relocated(t,a.build,requests,responses) # copied baseline must pass
  req=copy.deepcopy(requests);res=copy.deepcopy(responses);summary=json.loads((t/'relocate-results.json').read_text())
  if case=='template':
   b=bytearray((t/'relocate-template.bin').read_bytes());b[0]^=1;(t/'relocate-template.bin').write_bytes(b)
  elif case=='manifest':summary['manifest']['relocations'][0]+=4
  elif case in ('return_value','missing_entry'):
   i=next(i for i,p in enumerate(req) if struct.unpack_from('<I',p,8)[0]==13 and res[i][2]==0)
   if case=='return_value':res[i][5]^=1
   else:req.pop(i);res.pop(i)
  elif case=='base':
   i=next(i for i,p in enumerate(req) if struct.unpack_from('<I',p,8)[0]==14);res[i][5]^=16
  elif case=='summary_result':summary['runs'][-1]['value']^=1
  else:summary['runs'][-1]['base']^=16
  (t/'relocate-results.json').write_text(json.dumps(summary))
  try:prepare_relocated(t,a.build,req,res)
  except AssertionError:results.append(dict(case=case,rejected=True))
  else:raise AssertionError(('tampering accepted',case))
a.output.write_text(json.dumps(results,indent=2)+'\n');print('PASS: seven relocated capture mutations rejected')
