#!/usr/bin/env python3
"""Replay persistent reports and original paired captures without hardware."""
import argparse,gzip,hashlib,json,struct,subprocess,tempfile
from pathlib import Path
from live import Board
from run import verify_close
from test_native import compile_gate,pack
import wire

def verify(root,out,gate):
 code=(root/'persistirq/kernel.bin').read_bytes();module=(root/'persistirq-module-v2/dac960rtems.ko').read_bytes();ident=json.loads((out/'request.json').read_text())
 for k,data in [('payload_sha256',code),('image_sha256',wire.prepare(code)),('module_sha256',module)]:assert ident[k]==hashlib.sha256(data).hexdigest()
 original=(out/'open/stage-before-a5.bin').read_bytes();rows=json.loads((out/'reports.json').read_text());trace=gzip.decompress((out/'trace.bin.gz').read_bytes());pos=0;previous=None;identity=None;frozen=None;bad=[]
 for seq,row in enumerate(rows,1):
  gen,op,arg=row['request'];w=row['words'];raw=pack(w);request=struct.pack('<4I',0x31515250,gen,op,arg)
  elapsed,n=struct.unpack_from('<QI',trace,pos);pos+=12;assert elapsed>0 and n==16 and trace[pos:pos+n]==request;pos+=n
  size=struct.unpack_from('<I',trace,pos)[0];pos+=4;assert size==1280 and trace[pos:pos+size]==raw;pos+=size
  assert w[4]==seq and w[316:318]==[gen,arg] and subprocess.check_output([str(gate)],input=raw)==b'1'
  ids=w[60:64]+w[72:76]+w[288:291]
  if identity is None:identity=ids
  assert ids==identity
  if op in (1,2,3):
   ctl=json.loads((out/f'control-{seq:06d}.json').read_text());assert ctl['epoch']==seq and ctl['status'][4]==0x71000000|seq and ctl['reply'][6:8]==[0x75000000|seq,1]
   assert not ctl['reply'][3]&1 and not ctl['reply'][5]&1
  elif previous:assert w[8]==previous[8] and w[68:72]==previous[68:72]
  if op==1:
   assert w[44]==(0x10203040 if gen==1 else 0x22000000|(gen-1))
  if w[33]==4:
   if frozen is None:frozen=w[80:84]
   assert w[80:88]==frozen*2
   if previous and previous[33]==4:assert w[96:178]==previous[96:178]
  audit=out/f'audit-{seq:06d}.bin.gz'
  if audit.exists():
   image=gzip.decompress(audit.read_bytes())[:wire.bio.IMAGE_SIZE];before=wire.prepare(code)[:wire.bio.OFFSET]+wire.block(request,seq)+original[wire.bio.IMAGE_SIZE:]
   assert wire.response(before,image+original[len(image):])==(0,raw)
  for index in (17,18,19,20,21,22,23,24,25,27,28,29,32,33,39,49,50,51,56,57,58,59,64,65,68,71,76,77,78,79,91,103,104,185,186,280,281,282,283,288,289,290,292,293,294,318,319):
   x=w.copy();x[index]=0 if x[index] else 1;bad.append(pack(x))
  previous=w
 assert pos==len(trace) and subprocess.check_output([str(gate)],input=b''.join(bad))==b'0'*len(bad)
 early=(out/'early-close.json').exists();cap=out/('retained' if early else 'close');first=(cap/'payload-after-a5.bin').read_bytes()[:wire.bio.IMAGE_SIZE];second=(cap/'payload-after-5a.bin').read_bytes()[:wire.bio.IMAGE_SIZE];assert first==second
 before=wire.prepare(code)[:wire.bio.OFFSET]+wire.block(request,len(rows))+original[wire.bio.IMAGE_SIZE:];assert wire.response(before,first+original[len(first):])==(0,pack(previous))
 if early:
  e=json.loads((out/'early-close.json').read_text());assert e['retained']=='1,0,0,1,1,1,1,1' and e['rmmod_rc']
  log=(cap/'result.txt').read_text();assert 'PIRQ refuses restore before FINALIZE' in log and 'submit op=' not in log.split('PIRQ refuses restore before FINALIZE',1)[1]
  assert previous[36]==1 and previous[6]==2 and previous[7]==0
 else:
  assert previous[7]==1 and previous[36]==0;verify_close(cap)
  assert 'PIRQ FINALIZED: terminal resource proof and callback return' in (out/'last-step.txt').read_text()
 return dict(path=str(out),callbacks=len(rows),async_epochs=previous[294],clean_epochs=previous[293],follow_epochs=previous[295],early_close_retained=early,damaged_reports_rejected=len(bad),boot=ident['boot_id'])

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path);p.add_argument('paths',type=Path,nargs='+');a=p.parse_args()
 with tempfile.TemporaryDirectory() as tmp:gate=compile_gate(Path(tmp));results=[verify(a.root,o,gate) for o in a.paths]
 s=json.dumps(results,indent=2)+'\n';print(s,end='')
 if a.output:a.output.write_text(s)
if __name__=='__main__':main()
