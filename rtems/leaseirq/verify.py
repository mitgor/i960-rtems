#!/usr/bin/env python3
"""Replay original lease/control evidence with the exact host C report gate."""
import argparse,gzip,hashlib,json,struct,subprocess,tempfile
from pathlib import Path
from live import Board
from run import verify_close
from test_native import compile_gate
import wire

def verify(root,out,gate):
 code=(root/'leaseirq/kernel.bin').read_bytes();identity=json.loads((out/'request.json').read_text());mods=[p.read_bytes() for p in root.glob('leaseirq-module-*/dac960rtems.ko')];mod=next(data for data in mods if hashlib.sha256(data).hexdigest()==identity['module_sha256'])
 for k,data in [('payload_sha256',code),('image_sha256',wire.prepare(code)),('module_sha256',mod)]:assert identity[k]==hashlib.sha256(data).hexdigest()
 rows=json.loads((out/'reports.json').read_text());trace=gzip.decompress((out/'trace.bin.gz').read_bytes());pos=0;previous=None;ids=None;frozen=None;bad=[];epochs=[]
 original=(out/'open/stage-before-a5.bin').read_bytes()
 for seq,row in enumerate(rows,1):
  gen,op,arg=row['request'];request=struct.pack('<4I',0x31515250,gen,op,arg);w=row['words'];raw=struct.pack('<352I',*w)
  ns,n=struct.unpack_from('<QI',trace,pos);pos+=12;assert ns>0 and n==16 and trace[pos:pos+n]==request;pos+=n
  n=struct.unpack_from('<I',trace,pos)[0];pos+=4;assert n==1408 and trace[pos:pos+n]==raw;pos+=n
  assert w[4]==seq and w[316:318]==[gen,arg] and subprocess.check_output([str(gate)],input=raw)==b'1'
  cur=w[60:64]+w[72:76]+w[288:291]
  if ids is None:ids=cur
  assert ids==cur
  if w[33]==4:
   if frozen is None:frozen=w[80:84]
   assert w[80:88]==frozen*2
   if previous and previous[33]==4:assert w[96:178]==previous[96:178]
  if op in (1,2,3):
   c=json.loads((out/f'control-{seq:06d}.json').read_text());records=[r for r in c['records'] if 'reply' in r];renew=[r for r in records if r['action']==3];grants=[r for r in records if r['action']==2];stop=records[-1]
   assert stop['action']==1 and stop['reply'][6:8]==[0x75000000|seq,1]
   assert len(renew)==w[326] and len(grants)==int(c['grant'])
   for i,r in enumerate(renew,1):assert r['reply'][6:8]==[0x64000000|i,i]
   for r in records:assert r['reply'][2]==seq and not r['reply'][3]&1
   assert w[323]==(3 if c.get('cap') else 2 if c['expire'] else 1)
   if c['expire']:assert w[328]==512
   if c.get('cap'):assert w[347]-w[346]==24000
   errors=[r for r in c['records'] if 'errno' in r]
   if errors:
    # Captures originate on Linux; replay may run on macOS.
    assert sum(r['errno']==116 for r in errors)==3
    assert sum(r['errno']==1 for r in errors)==1
    assert sum(r['errno']==114 for r in errors)==int(c['grant'])
   duration=stop['seconds']-(grants[0]['seconds'] if grants else records[0]['seconds'])
   if c['silent']:assert len(records[records.index(grants[0])+1:])==1 and duration>=c['duration']
   if c['duration']>=10:assert duration>=c['duration'] and w[347]-w[324]>c['duration']*180
   epochs.append(dict(sequence=seq,reason=w[323],renewals=w[326],lease_ticks=w[347]-w[346],control_seconds=duration,hardware_checks=w[330],owner_irq_entries=w[104],other_irq_entries=w[186]))
  elif previous:assert w[8]==previous[8]
  if op==1:assert w[44]==(0x10203040 if gen==1 else 0x22000000|(gen-1))
  audit=out/f'audit-{seq:06d}.bin.gz'
  if audit.exists():
   log=(out/f'audit-{seq:06d}.txt').read_text();q=log.index('LEASE QUIESCED');start=log.rfind('submit op=6f',0,q);window=log[start:q]
   assert start>=0 and window.count('submit op=')==1 and 'complete op=' not in window
   assert log.index('CONCURRENT window closed/joined rc=0 done=1',q)<log.index('complete op=6f',q)
   image=gzip.decompress(audit.read_bytes())[:wire.bio.IMAGE_SIZE];before=wire.prepare(code)[:wire.bio.OFFSET]+wire.block(request,seq)+original[wire.bio.IMAGE_SIZE:];assert wire.response(before,image+original[len(image):])==(0,raw)
  indices=[17,18,19,20,21,22,23,24,25,27,28,29,32,33,39,49,50,51,56,57,58,59,64,65,68,71,76,77,78,79,91,103,104,185,186,280,281,282,283,288,289,290,292,293,294,318,319,320,321,322,323,327,328,331,332,333,334,335,336,337,339,340,341,342,343,344,345,349,350,351]
  for index in indices:
   x=w.copy();x[index]=0 if x[index] else 1;bad.append(struct.pack('<352I',*x))
  previous=w
 assert pos==len(trace) and subprocess.check_output([str(gate)],input=b''.join(bad))==b'0'*len(bad)
 assert previous[7] and not previous[36];verify_close(out/'close')
 first=(out/'close/payload-after-a5.bin').read_bytes()[:wire.bio.IMAGE_SIZE];assert first==(out/'close/payload-after-5a.bin').read_bytes()[:wire.bio.IMAGE_SIZE]
 before=wire.prepare(code)[:wire.bio.OFFSET]+wire.block(request,len(rows))+original[wire.bio.IMAGE_SIZE:];assert wire.response(before,first+original[len(first):])==(0,raw)
 log=(out/'last-step.txt').read_text();assert 'PIRQ FINALIZED' in log
 return dict(path=str(out),callbacks=len(rows),epochs=epochs,corruptions_rejected=len(bad),boot=identity['boot_id'])
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path);p.add_argument('paths',type=Path,nargs='+');a=p.parse_args()
 with tempfile.TemporaryDirectory() as tmp:gate=compile_gate(Path(tmp));rows=[verify(a.root,out,gate) for out in a.paths]
 s=json.dumps(rows,indent=2)+'\n';print(s,end='')
 if a.output:a.output.write_text(s)
if __name__=='__main__':main()
