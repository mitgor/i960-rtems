#!/usr/bin/env python3
"""Tamper-test the accepted shared-arena capture without changing its source."""
import argparse,json,shutil,struct,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
r=Path(__file__).resolve().parent;results=[]
for name in ('magic','phase','timeout','recursive','owner-handle','report','uploaded-byte'):
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);cap=root/'capture';shutil.copytree(a.capture,cap)
  if name=='report':
   f=cap/'doom-shared.json';j=json.loads(f.read_text());j['wrong_task_rejections']=0;f.write_text(json.dumps(j))
  elif name=='uploaded-byte':
   f=cap/'uploaded-data.bin';b=bytearray(f.read_bytes());b[-1]^=1;f.write_bytes(b)
  else:
   f=cap/'upload-journal.jsonl';rows=[json.loads(l) for l in f.read_text().splitlines()];pending=None;changed=False
   for row in rows:
    req=bytes.fromhex(row['request']);op=struct.unpack_from('<I',req)[0]
    if op==1:pending=struct.unpack_from('<8I',req,32)
    elif pending and 'response' in row:
     b=bytearray.fromhex(row['response']);w=struct.unpack_from('<16I',b,32)
     if not w[3] and w[1]==pending[1]:
      index={'magic':0,'phase':1,'timeout':8,'recursive':9}.get(name)
      if (pending[2]==9 and pending[3]==index) or (name=='owner-handle' and pending[2]==8):
       at=32+4*(15 if name=='owner-handle' else 5);struct.pack_into('<I',b,at,struct.unpack_from('<I',b,at)[0]^1);row['response']=b.hex();changed=True;break
      pending=None
   assert changed;f.write_text(''.join(json.dumps(row)+'\n' for row in rows))
  run=subprocess.run(['python3',str(r/'verify_upload.py'),str(cap),'--doom-heap','--doom-shared','--output',str(root/'out.json')],capture_output=True,text=True)
  assert run.returncode!=0,name
  results.append(dict(case=name,rejected=True,error=run.stderr.splitlines()[-1]))
a.output.write_text(json.dumps(results,indent=2)+'\n');print('PASS: seven shared capture mutations rejected')
