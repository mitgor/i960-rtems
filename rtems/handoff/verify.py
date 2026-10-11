#!/usr/bin/env python3
"""Replay archived callback-free monitor evidence; never accesses hardware."""
import argparse,gzip,hashlib,json,struct
from pathlib import Path
from live import decode
from run import verify_close,ROM_SHA
import wire

def verify(root,out):
 code=(root/'handoff/kernel.bin').read_bytes();mods=[p.read_bytes() for p in root.glob('handoff-module-*/dac960auto.ko')]
 ident=json.loads((out/'request.json').read_text());mod=next(m for m in mods if hashlib.sha256(m).hexdigest()==ident['module_sha256'])
 for k,data in [('payload_sha256',code),('image_sha256',wire.prepare(code)),('module_sha256',mod)]:assert ident[k]==hashlib.sha256(data).hexdigest()
 events=json.loads((out/'controls.json').read_text());assert len(events)==8 and events[0]['errno']==116
 good=events[1:];assert [r['op'] for r in good]==[1,0,0,0,2,1,3]
 assert [r['hold'] for r in good[1:4]]==[0,5,20]
 epoch=good[0]['epoch'];tags={0:0x87000000,1:0x85000000,2:0x86000000,3:0x89000000}
 for r in good:
  w=r['words'];assert r['epoch']==epoch and w==[r['op'],epoch,r['hold'],1,w[4],tags[r['op']]|epoch,0,0] and not w[4]&1
 trace=gzip.decompress((out/'trace.bin.gz').read_bytes());pos=0;responses=[]
 for seq,op in enumerate((1,0),1):
  ns,n=struct.unpack_from('<QI',trace,pos);pos+=12;req=trace[pos:pos+n];pos+=n
  assert ns>0 and req==struct.pack('<4I',0x31415452,op,epoch,0)
  n=struct.unpack_from('<I',trace,pos)[0];pos+=4;raw=trace[pos:pos+n];pos+=n;assert n==256;responses.append(raw)
 assert pos==len(trace)
 assert struct.unpack_from('<I',responses[0],60)[0]==1
 report=decode(responses[1],4,2,1);assert responses[1]==(out/'report.bin').read_bytes()
 assert report[24]==1 and report[27]==epoch and report[21]==1000000
 original=(out/'open/stage-before-a5.bin').read_bytes()
 assert hashlib.sha256(original).hexdigest()==ROM_SHA
 image=gzip.decompress((out/'audit-000001.bin.gz').read_bytes())
 before=wire.prepare(code)[:wire.bio.OFFSET]+wire.block(struct.pack('<4I',0x31415452,1,epoch,0),1)+original[wire.bio.IMAGE_SIZE:]
 assert wire.response(before,image+original[len(image):])==(0,responses[0])
 log=(out/'monitor-log.txt').read_text();window=log[log.index('MONITOR enter'):]
 assert 'submit op=' not in window and window.count('MONITOR returned')==7
 verify_close(out/'close');assert 'AUTONOMOUS STOP verified before any RAM restoration' in (out/'close/result.txt').read_text()
 summary=json.loads((out/'summary.json').read_text());assert summary['restored'] and summary['unloaded'] and summary['steps']==2
 # Ensure key report corruption cannot pass the offline contract.
 mutations=0
 for index in [0,1,7,8,9,11,12,13,15,16,17,18,19,20,22,24,25,26,43,44,45,46,48,53,54]:
  w=report.copy();w[index]=0 if w[index] else 1
  try:decode(struct.pack('<64I',*w),4,2,1)
  except AssertionError:mutations+=1
  else:raise AssertionError(('corrupt report accepted',index))
 return dict(path=str(out.relative_to(root)),boot=ident['boot_id'],entries=4,denials=2,expired=1,report_mutations_rejected=mutations)

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args()
 rows=[verify(a.root,path) for path in sorted(a.root.glob('handoff-v*-live/run-*'))];assert len(rows)==5
 print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
