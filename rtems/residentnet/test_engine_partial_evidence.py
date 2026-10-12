#!/usr/bin/env python3
"""Baseline first: mutate the failed physical prefix without claiming acceptance."""
import argparse,copy,json,struct,tempfile
from pathlib import Path
from engine_replay import prepare
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--build',type=Path,required=True);p.add_argument('--wad',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();rq=[];rs=[];pending=None
for e in map(json.loads,(a.capture/'upload-journal.jsonl').read_text().splitlines()):
 if 'errno' in e:continue
 q=bytes.fromhex(e['request']);op,n=struct.unpack_from('<I',q)[0],struct.unpack_from('<I',q,8)[0]
 if op==1:pending=q[32:32+n];rq.append(pending)
 elif pending:
  w=list(struct.unpack_from('<16I',bytes.fromhex(e['response']),32))
  if not w[3] and w[1]==struct.unpack_from('<I',pending,4)[0]:rs.append(w);pending=None
assert not pending and len(rq)==len(rs);prepare(a.capture,a.build,a.wad,rq,rs,partial=True);result=[]
for case in ('identity','metadata','wire_code','wire_metadata','wire_reply','missing_refusal','irq_bit'):
 with tempfile.TemporaryDirectory() as d:
  t=Path(d);capture=t/'capture';build=t/'build';capture.mkdir();build.mkdir()
  (capture/'snapshots.json').write_bytes((a.capture/'snapshots.json').read_bytes())
  for name in ('manifest.json','template.bin','relocations.bin'):(build/name).write_bytes((a.build/name).read_bytes())
  q=list(rq);r=copy.deepcopy(rs);prepare(capture,build,a.wad,q,r,partial=True)
  if case=='identity':m=json.loads((build/'manifest.json').read_text());m['template_sha256']='0'*64;(build/'manifest.json').write_text(json.dumps(m))
  elif case=='metadata':b=bytearray((build/'relocations.bin').read_bytes());b[0]^=1;(build/'relocations.bin').write_bytes(b)
  elif case=='irq_bit':rows=json.loads((capture/'snapshots.json').read_text());rows[-1]['words'][11]=0;(capture/'snapshots.json').write_text(json.dumps(rows))
  elif case=='wire_reply':i=next(i for i,p in enumerate(q) if struct.unpack_from('<I',p,8)[0]==18 and r[i][2]==2);r[i][2]=0
  elif case=='missing_refusal':i=next(i for i,p in enumerate(q) if struct.unpack_from('<I',p,8)[0]==18 and r[i][2]==2);q.pop(i);r.pop(i)
  else:
   start=next(i for i,p in enumerate(q) if struct.unpack_from('<I',p,8)[0]==1 and struct.unpack_from('<I',p,36)[0]==4);segment=3 if case=='wire_metadata' else 0;i=next(i for i in range(start+1,len(q)) if struct.unpack_from('<2I',q[i],8)==(2,segment));b=bytearray(q[i]);b[32]^=1;q[i]=bytes(b)
  try:prepare(capture,build,a.wad,q,r,partial=True)
  except AssertionError:result.append(dict(case=case,rejected=True))
  else:raise AssertionError(('partial evidence tampering accepted',case))
a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS: seven failed-prefix evidence mutations rejected; no positive engine acceptance')
