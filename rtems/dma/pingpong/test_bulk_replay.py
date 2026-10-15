#!/usr/bin/env python3
"""Legacy-to-bulk replay compatibility and new operation tamper rejection."""
import argparse,json,shutil,struct,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'residentnet'))
from verify_play_pipeline import verify
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args()
verify(a.capture)
with tempfile.TemporaryDirectory() as t:
 d=Path(t)/'capture';shutil.copytree(a.capture,d)
 path=d/'pingpong-journal.jsonl';rows=[json.loads(x) for x in path.read_text().splitlines()];out=[];i=0
 while i<len(rows):
  row=rows[i];q=bytes.fromhex(row.get('request',''))
  if q and struct.unpack_from('<I',q)[0]==3:
   batch=rows[i:i+72];h=list(struct.unpack_from('<8I',q));assert h[3]==0
   for j,e in enumerate(batch):
    x=list(struct.unpack_from('<8I',bytes.fromhex(e['request'])));assert x[:3]==h[:3] and x[3]==j*1024
   h[0]=8;h[3]=73728;head=struct.pack('<8I',*h)
   out.append(dict(request=(head+bytes(73728)).hex(),response=(head+b''.join(bytes.fromhex(e['response'])[32:] for e in batch)).hex(),ns=sum(e['ns'] for e in batch)));i+=72
  else:out.append(row);i+=1
 def save(v):path.write_text(''.join(json.dumps(x)+'\n' for x in v))
 save(out);verify(d)
 idx=next(i for i,r in enumerate(out) if bytes.fromhex(r.get('request',''))[:4]==struct.pack('<I',8))
 for kind in ('short','length','guard','payload','marker','missing'):
  v=[dict(x) for x in out];e=v[idx]
  if kind=='missing':v.pop(idx)
  elif kind=='short':e['response']=e['response'][:-2]
  elif kind=='length':
   for key in ('request','response'):
    b=bytearray.fromhex(e[key]);struct.pack_into('<I',b,12,65536);e[key]=b.hex()
  else:
   b=bytearray.fromhex(e['response']);b[32+dict(guard=0,payload=4096,marker=73724)[kind]]^=1;e['response']=b.hex()
  save(v)
  try:verify(d)
  except (AssertionError,IndexError,KeyError,ValueError):pass
  else:raise AssertionError('accepted '+kind)
print('PASS legacy/bulk replay equivalence and six bulk journal mutations rejected')
