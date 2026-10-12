#!/usr/bin/env python3
"""Mutated owned invocation/control evidence must fail an independent oracle."""
import argparse,json,struct,tempfile
from pathlib import Path
from owned_replay import prepare
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
requests=[];responses=[];pending=None
for e in map(json.loads,(a.capture/'upload-journal.jsonl').read_text().splitlines()):
 if 'errno' in e:continue
 req=bytes.fromhex(e['request']);op,n=struct.unpack_from('<I',req)[0],struct.unpack_from('<I',req,8)[0]
 if op==1:pending=req[32:32+n];requests.append(pending)
 elif pending:
  w=list(struct.unpack_from('<16I',bytes.fromhex(e['response']),32))
  if not w[3] and w[1]==struct.unpack_from('<I',pending,4)[0]:responses.append(w);pending=None
assert not pending and len(requests)==len(responses)
prepare(a.capture,a.build,requests,responses);results=[]
for case in ('template','magic','generation','missing_stop','refusal','running','result','seed','extra_stop'):
 with tempfile.TemporaryDirectory() as tmp:
  t=Path(tmp)
  for name in ('owned-results.json','owned-template.bin','owned-journal.jsonl','upload-journal.jsonl'):(t/name).write_bytes((a.capture/name).read_bytes())
  if (a.capture/'engine-results.json').exists():(t/'engine-results.json').write_bytes((a.capture/'engine-results.json').read_bytes())
  prepare(t,a.build,requests,responses)
  summary=json.loads((t/'owned-results.json').read_text());rows=[json.loads(s) for s in (t/'owned-journal.jsonl').read_text().splitlines()]
  if case=='template':
   b=bytearray((t/'owned-template.bin').read_bytes());b[0]^=1;(t/'owned-template.bin').write_bytes(b)
  elif case in ('magic','generation','missing_stop','extra_stop'):
   i=next(i for i,e in enumerate(rows) if e['op']==6 and 'errno' not in e)
   if case=='missing_stop':rows.pop(i)
   elif case=='extra_stop':rows.insert(i,rows[i].copy())
   else:b=bytearray.fromhex(rows[i]['request']);b[32 if case=='magic' else 36]^=1;rows[i]['request']=b.hex()
  elif case=='refusal':next(e for e in rows if 'errno' in e)['errno']=22
  elif case=='running':
   e=next(e for e in rows if e['op']==5 and struct.unpack_from('<I',bytes.fromhex(e['response']),40)[0]==1);b=bytearray.fromhex(e['response']);struct.pack_into('<I',b,40,3);e['response']=b.hex()
  elif case=='result':summary['runs'][1]['value']^=1
  else:summary['runs'][0]['result'][0]^=1
  (t/'owned-results.json').write_text(json.dumps(summary));(t/'owned-journal.jsonl').write_text('\n'.join(json.dumps(e) for e in rows)+'\n')
  try:prepare(t,a.build,requests,responses)
  except AssertionError:results.append(dict(case=case,rejected=True))
  else:raise AssertionError(('owned tampering accepted',case))
a.output.write_text(json.dumps(results,indent=2)+'\n');print('PASS: nine owned control/exit evidence mutations rejected')
