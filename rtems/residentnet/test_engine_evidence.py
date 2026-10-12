#!/usr/bin/env python3
import argparse,copy,json,struct,tempfile
from pathlib import Path
from engine_replay import prepare
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--build',type=Path,required=True);p.add_argument('--wad',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();requests=[];responses=[];pending=None
for e in map(json.loads,(a.capture/'upload-journal.jsonl').read_text().splitlines()):
 if 'errno' in e:continue
 q=bytes.fromhex(e['request']);op,n=struct.unpack_from('<I',q)[0],struct.unpack_from('<I',q,8)[0]
 if op==1:pending=q[32:32+n];requests.append(pending)
 elif pending:
  w=list(struct.unpack_from('<16I',bytes.fromhex(e['response']),32))
  if not w[3] and w[1]==struct.unpack_from('<I',pending,4)[0]:responses.append(w);pending=None
assert not pending and len(requests)==len(responses);prepare(a.capture,a.build,a.wad,requests,responses);results=[]
for case in ('template','metadata','identity','frame','cleanup','peak','stop_generation','missing_stop','wad_payload','wire_code','wire_reply'):
 with tempfile.TemporaryDirectory() as tmp:
  t=Path(tmp)
  for name in ('engine-results.json','engine-template.bin','engine-relocations.bin','engine-owned-journal.jsonl','engine-wad-journal.jsonl','cache-results.json'):(t/name).write_bytes((a.capture/name).read_bytes())
  prepare(t,a.build,a.wad,requests,responses);r=json.loads((t/'engine-results.json').read_text());rq=list(requests);rs=copy.deepcopy(responses)
  if case in ('template','metadata'):
   f=t/('engine-template.bin' if case=='template' else 'engine-relocations.bin');b=bytearray(f.read_bytes());b[0]^=1;f.write_bytes(b)
  elif case=='identity':r['wad_sha256']='0'*64
  elif case in ('frame','cleanup','peak'):r['runs'][0]['result'][{'frame':3,'cleanup':10,'peak':7}[case]]^=1
  elif case in ('stop_generation','missing_stop'):
   rows=[json.loads(s) for s in (t/'engine-owned-journal.jsonl').read_text().splitlines()];i=next(i for i,e in enumerate(rows) if e['op']==6 and 'errno' not in e)
   if case=='missing_stop':rows.pop(i)
   else:b=bytearray.fromhex(rows[i]['request']);b[36]^=1;rows[i]['request']=b.hex()
   (t/'engine-owned-journal.jsonl').write_text('\n'.join(json.dumps(e) for e in rows)+'\n')
  elif case=='wad_payload':
   rows=[json.loads(s) for s in (t/'engine-wad-journal.jsonl').read_text().splitlines()];i=next(i for i,e in enumerate(rows) if e['op']==4);b=bytearray.fromhex(rows[i]['request']);b[64]^=1;rows[i]['request']=b.hex();(t/'engine-wad-journal.jsonl').write_text('\n'.join(json.dumps(e) for e in rows)+'\n')
  elif case=='wire_reply':i=next(i for i,q in enumerate(rq) if struct.unpack_from('<I',q,8)[0]==19);rs[i][5]^=1
  else:
   begin=next(i for i,q in enumerate(rq) if struct.unpack_from('<I',q,8)[0]==1 and struct.unpack_from('<I',q,36)[0]==4);i=next(i for i in range(begin+1,len(rq)) if struct.unpack_from('<I',rq[i],8)[0]==2);b=bytearray(rq[i]);b[32]^=1;rq[i]=bytes(b)
  (t/'engine-results.json').write_text(json.dumps(r))
  try:prepare(t,a.build,a.wad,rq,rs)
  except AssertionError:results.append(dict(case=case,rejected=True))
  else:raise AssertionError(('engine tampering accepted',case))
a.output.write_text(json.dumps(results,indent=2)+'\n');print('PASS: 11 engine admission/output/STOP/WAD evidence mutations rejected')
