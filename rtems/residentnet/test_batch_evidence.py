#!/usr/bin/env python3
"""Mutation rejection for the independent WAB1 acceptance oracle."""
import argparse,copy,json,struct,tempfile
from pathlib import Path
from batch_replay import prepare
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--build',type=Path,required=True);p.add_argument('--wad',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();requests=[];responses=[];pending=None
for e in map(json.loads,(a.capture/'upload-journal.jsonl').read_text().splitlines()):
 if 'errno' in e:continue
 q=bytes.fromhex(e['request']);op,n=struct.unpack_from('<I',q)[0],struct.unpack_from('<I',q,8)[0]
 if op==1:pending=q[32:32+n];requests.append(pending)
 elif pending:
  w=list(struct.unpack_from('<16I',bytes.fromhex(e['response']),32))
  if not w[3] and w[1]==struct.unpack_from('<I',pending,4)[0]:responses.append(w);pending=None
assert not pending;prepare(a.capture,a.wad,a.build,requests,responses);results=[]
for case in ('identity','oracle','limit','report','stop_generation','template','payload','crc','offset','sequence','length','wanted','drop_fragment','duplicate_fragment','reorder_fragments','stop_stale','missing_stop','wire_result'):
 with tempfile.TemporaryDirectory() as d:
  t=Path(d)
  for name in ('batch-results.json','batch-wad-journal.jsonl','batch-owned-journal.jsonl','cache-template.bin','engine-results.json'):(t/name).write_bytes((a.capture/name).read_bytes())
  prepare(t,a.wad,a.build,requests,responses);r=json.loads((t/'batch-results.json').read_text());rs=copy.deepcopy(responses)
  if case=='identity':r['wad_sha256']='0'*64
  elif case=='oracle':r['oracle']^=1
  elif case=='limit':r['runs'][0]['limit']=4096
  elif case=='report':r['runs'][-1]['report'][5]=1
  elif case=='stop_generation':r['stop_generation']+=1
  elif case=='template':b=bytearray((t/'cache-template.bin').read_bytes());b[0]^=1;(t/'cache-template.bin').write_bytes(b)
  elif case=='wire_result':i=next(i for i,q in enumerate(requests) if struct.unpack_from('<I',q,8)[0]==22);rs[i][5]^=1
  else:
   name='batch-owned-journal.jsonl' if case in ('stop_stale','missing_stop') else 'batch-wad-journal.jsonl';rows=[json.loads(s) for s in (t/name).read_text().splitlines()];indices=[i for i,e in enumerate(rows) if e['op']==(6 if name.startswith('batch-owned') else 4) and 'errno' not in e];i=indices[-1] if name.startswith('batch-owned') else indices[0]
   if case in ('drop_fragment','missing_stop'):rows.pop(i)
   elif case=='duplicate_fragment':rows.insert(i,copy.deepcopy(rows[i]))
   elif case=='reorder_fragments':rows[indices[0]],rows[indices[1]]=rows[indices[1]],rows[indices[0]]
   else:
    b=bytearray.fromhex(rows[i]['request']);b[{'payload':64,'crc':56,'offset':44,'sequence':36,'length':48,'wanted':60,'stop_stale':36}[case]]^=1;rows[i]['request']=b.hex()
   (t/name).write_text('\n'.join(map(json.dumps,rows))+'\n')
  (t/'batch-results.json').write_text(json.dumps(r))
  try:prepare(t,a.wad,a.build,requests,rs)
  except AssertionError:results.append(dict(case=case,rejected=True))
  else:raise AssertionError(('batch evidence mutation accepted',case))
a.output.write_text(json.dumps(results,indent=2)+'\n');print('PASS: 18 batch identity/limit/result/fragment/order/STOP evidence mutations rejected')
