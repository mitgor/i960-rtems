#!/usr/bin/env python3
"""Reject tampered first-frame, authenticated image, WAB1 and STOP evidence."""
import argparse,copy,json,struct,tempfile,zlib
from pathlib import Path
from engine_replay import prepare
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--build',type=Path,required=True);p.add_argument('--wad',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();requests=[];responses=[];pending=None
for line in (a.capture/'upload-journal.jsonl').read_text().splitlines():
 e=json.loads(line)
 if 'errno' in e:continue
 q=bytes.fromhex(e['request']);op,n=struct.unpack_from('<I',q)[0],struct.unpack_from('<I',q,8)[0]
 if op==1:pending=q[32:32+n];requests.append(pending)
 elif pending:
  w=list(struct.unpack_from('<16I',bytes.fromhex(e['response']),32))
  if not w[3] and w[1]==struct.unpack_from('<I',pending,4)[0]:responses.append(w);pending=None
assert not pending;prepare(a.capture,a.build,a.wad,requests,responses);results=[]
for case in ('template','metadata','identity','frame','palette','cleanup','peak','stop_generation','missing_stop','payload','sequence','offset','length','total','crc','drop_fragment','duplicate_fragment','wire_code','wire_reply','request_trace'):
 with tempfile.TemporaryDirectory() as d:
  t=Path(d)
  for name in ('engine-results.json','engine-template.bin','engine-relocations.bin','engine-owned-journal.jsonl','engine-wad-journal.jsonl'):(t/name).symlink_to((a.capture/name).resolve())
  for name in ('engine-checkpoint-journal.jsonl','startup-checkpoints.jsonl'):
   if (a.capture/name).exists():(t/name).symlink_to((a.capture/name).resolve())
  r=json.loads((t/'engine-results.json').read_text());rq=list(requests);rs=copy.deepcopy(responses)
  def write(name,data):
   f=t/name;f.unlink();f.write_bytes(data)
  if case in ('template','metadata'):
   name='engine-template.bin' if case=='template' else 'engine-relocations.bin';b=bytearray((t/name).read_bytes());b[0]^=1;write(name,b)
  elif case=='identity':r['wad_sha256']='0'*64
  elif case in ('frame','palette','cleanup','peak'):r['runs'][0]['result'][{'frame':3,'palette':4,'cleanup':10,'peak':7}[case]]^=1
  elif case=='stop_generation':r['runs'][1]['control'][1]+=1
  elif case=='request_trace':r['requests'][0]['offset']+=512
  elif case=='wire_reply':i=next(i for i,q in enumerate(rq) if struct.unpack_from('<I',q,8)[0]==19);rs[i][5]^=1
  elif case=='wire_code':
   begin=next(i for i,q in enumerate(rq) if struct.unpack_from('<I',q,8)[0]==1 and struct.unpack_from('<I',q,36)[0]==4);i=next(i for i in range(begin+1,len(rq)) if struct.unpack_from('<I',rq[i],8)[0]==2);b=bytearray(rq[i]);b[32]^=1;rq[i]=bytes(b)
  else:
   name='engine-owned-journal.jsonl' if case=='missing_stop' else 'engine-wad-journal.jsonl'
   original=(t/name).resolve();(t/name).unlink();changed=False
   with original.open() as source,(t/name).open('w') as dest:
    for line in source:
     e=json.loads(line)
     if changed or e['op']!=(6 if case=='missing_stop' else 4) or 'errno' in e:dest.write(line);continue
     changed=True
     if case in ('missing_stop','drop_fragment'):continue
     if case=='duplicate_fragment':dest.write(line);dest.write(line);continue
     # Change both echo and request. For payload tampering, also repair its
     # CRC: only comparison with the pinned WAD can reject that forged data.
     offset={'payload':64,'sequence':36,'offset':44,'length':48,'total':60,'crc':56}[case]
     for key in ('request','response'):
      b=bytearray.fromhex(e[key]);b[offset]^=1
      if case=='payload':size=struct.unpack_from('<I',b,48)[0];struct.pack_into('<I',b,56,zlib.crc32(b[64:64+size]))
      e[key]=b.hex()
     dest.write(json.dumps(e)+'\n')
   assert changed
  write('engine-results.json',json.dumps(r).encode())
  try:prepare(t,a.build,a.wad,rq,rs)
  except AssertionError:results.append(dict(case=case,rejected=True))
  else:raise AssertionError(('startup evidence mutation accepted',case))
a.output.write_text(json.dumps(results,indent=2)+'\n');print('PASS 20 startup evidence mutations rejected after a clean baseline')
