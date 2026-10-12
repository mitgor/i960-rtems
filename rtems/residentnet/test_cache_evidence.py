#!/usr/bin/env python3
"""Reject altered physical cache evidence against the independent wire oracle."""
import argparse,copy,json,struct,tempfile
from pathlib import Path
from cache_replay import prepare
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--wad',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
requests=[];responses=[];pending=None
for e in map(json.loads,(a.capture/'upload-journal.jsonl').read_text().splitlines()):
 if 'errno' in e:continue
 req=bytes.fromhex(e['request']);op,n=struct.unpack_from('<I',req)[0],struct.unpack_from('<I',req,8)[0]
 if op==1:pending=req[32:32+n];requests.append(pending)
 elif pending:
  w=list(struct.unpack_from('<16I',bytes.fromhex(e['response']),32))
  if not w[3] and w[1]==struct.unpack_from('<I',pending,4)[0]:responses.append(w);pending=None
assert not pending and len(requests)==len(responses)
prepare(a.capture,a.wad,a.build,requests,responses)
results=[]
for case in ('template','identity','oracle','report','request_offset','payload','crc','missing_reply','run_result'):
 with tempfile.TemporaryDirectory() as tmp:
  t=Path(tmp)
  for name in ('cache-results.json','cache-template.bin','wad-journal.jsonl'):(t/name).write_bytes((a.capture/name).read_bytes())
  if (a.capture/'owned-results.json').exists():(t/'owned-results.json').write_bytes((a.capture/'owned-results.json').read_bytes())
  if (a.capture/'batch-results.json').exists():(t/'batch-results.json').write_bytes((a.capture/'batch-results.json').read_bytes())
  if (a.capture/'engine-results.json').exists():(t/'engine-results.json').write_bytes((a.capture/'engine-results.json').read_bytes())
  prepare(t,a.wad,a.build,requests,responses) # copied baseline must pass
  r=json.loads((t/'cache-results.json').read_text())
  if case=='template':
   b=bytearray((t/'cache-template.bin').read_bytes());b[0]^=1;(t/'cache-template.bin').write_bytes(b)
  elif case in ('payload','crc','missing_reply'):
   rows=[json.loads(s) for s in (t/'wad-journal.jsonl').read_text().splitlines()]
   i=next(i for i,row in enumerate(rows) if row['op']==4 and struct.unpack_from('<I',bytes.fromhex(row['request']),36)[0]>10)
   if case=='missing_reply':rows.pop(i)
   else:b=bytearray.fromhex(rows[i]['request']);b[64 if case=='payload' else 56]^=1;rows[i]['request']=b.hex()
   (t/'wad-journal.jsonl').write_text('\n'.join(json.dumps(row) for row in rows)+'\n')
  elif case=='identity':r['wad_sha256']='0'*64
  elif case=='oracle':r['oracle']^=1
  elif case=='report':r['report'][2]+=1
  elif case=='request_offset':r['requests'][0]['offset']+=512
  else:r['runs'][0]['result']^=1
  (t/'cache-results.json').write_text(json.dumps(r))
  try:prepare(t,a.wad,a.build,requests,responses)
  except AssertionError:results.append(dict(case=case,rejected=True))
  else:raise AssertionError(('accepted cache mutation',case))
a.output.write_text(json.dumps(results,indent=2)+'\n');print('PASS: nine cache evidence mutations rejected')
