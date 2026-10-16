#!/usr/bin/env python3
"""Explicit RAM-only RTEMS session runner. No flash writes; no retries."""
import argparse,fcntl,gzip,hashlib,json,os,struct,subprocess,time
from pathlib import Path
import wire
from card_select import select
DBG=Path('/sys/kernel/debug/dac960rtems')
ROM_SHA='a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0'
def sha(data):return hashlib.sha256(data).hexdigest()
def capture(out,debugfs=DBG):
 out.mkdir()
 for p in debugfs.iterdir():
  if p.is_file():(out/p.name).write_bytes(p.read_bytes())
def verify_close(out):
 before=(out/'stage-before-a5.bin').read_bytes()
 assert len(before)==524288 and sha(before)==ROM_SHA
 for n in ['stage-before-5a.bin','stage-restored-a5.bin','stage-restored-5a.bin']:assert (out/n).read_bytes()==before,n
 assert 'SESSION CLOSE rc=0 pending=0 exec-dirty=0 stage-dirty=0' in (out/'result.txt').read_text()
 for names in [ ['rom-table-a5.bin','rom-table-5a.bin','exec-table-restored-a5.bin','exec-table-restored-5a.bin'],['exec-ram-before-a5.bin','exec-ram-before-5a.bin','exec-ram-restored-a5.bin','exec-ram-restored-5a.bin'],['exec-flash-before-a5.bin','exec-flash-before-5a.bin','exec-flash-restored-a5.bin','exec-flash-restored-5a.bin'],['upload-test.bin','upload-restore.bin','exec-flash-followup.bin','exec-stock-followup.bin'] ]:
  assert len({(out/n).read_bytes() for n in names})==1,names

class Board:
 def __init__(self,payload,module,out,autonomous=False,module_options=(),bdf=None):
  self.identity=select(bdf,'dac960pg');self.bdf=bdf
  if self.identity['driver'] is not None:raise ValueError('selected card already has a driver')
  if any(x.startswith('bdf=') for x in module_options):raise ValueError('BDF cannot be overridden through module_options')
  self.autonomous=autonomous;self.module_name="dac960auto" if autonomous else "dac960rtems";self.debugfs=Path("/sys/kernel/debug")/self.module_name
  self.out=out;self.fd=None;self.lock=None;self.sequence=0;self.records=None;self.timings=[]
  self.code=payload.read_bytes();self.image=wire.prepare(self.code)
  out.mkdir(parents=True,exist_ok=False)
  self.lock=open('/run/lock/i960-loadrun.lock','w');fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  self.identity=select(self.bdf,'dac960pg')
  if self.identity['driver'] is not None:raise ValueError('selected card acquired a driver')
  assert not any(Path('/sys/module',m).exists() for m in ['dac960dump','dac960loadrun','dac960program','dac960session','dac960rtems','dac960auto'])
  name='i960/rtems-'+sha(self.image)+'.bin';fw=Path('/lib/firmware')/name;fw.parent.mkdir(exist_ok=True)
  if fw.exists():assert fw.read_bytes()==self.image
  else:fw.write_bytes(self.image)
  (out/'request.json').write_text(json.dumps(dict(card=self.identity,payload_sha256=sha(self.code),image_sha256=sha(self.image),module_sha256=sha(module.read_bytes()),autonomous=autonomous,module_options=list(module_options),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()),indent=2)+'\n')
  subprocess.run(['insmod',str(module),'bdf='+self.bdf,'firmware_name='+name,'pointer_check=1','runtime_check=1','stage_check=1','buffer_io=1',f'payload_argument={wire.bio.BASE}',*module_options],check=True)
  capture(out/'preflight',self.debugfs)
  assert 'experiment-result=0 pending=0;' in (out/'preflight/result.txt').read_text()
  self.fd=os.open('/dev/i960-auto' if autonomous else '/dev/i960-rtems',os.O_RDWR|os.O_CLOEXEC)
  capture(out/'open',self.debugfs);self.original=(out/'open/stage-before-a5.bin').read_bytes()
  self.records=gzip.open(out/'trace.bin.gz','wb')
 def step(self,incoming):
  self.sequence+=1;b=wire.block(incoming,self.sequence);t=time.monotonic_ns()
  try:assert os.write(self.fd,b)==len(b)
  except BaseException:
   capture(self.out/f'failure-{self.sequence:06d}',self.debugfs);raise
  reply=os.read(self.fd,wire.bio.SIZE);elapsed=time.monotonic_ns()-t
  assert len(reply)==wire.bio.SIZE
  before=self.image[:wire.bio.OFFSET]+b+self.original[wire.bio.IMAGE_SIZE:]
  after=self.debugfs.joinpath('payload-after-a5.bin').read_bytes()
  second=self.debugfs.joinpath('payload-after-5a.bin').read_bytes()
  if self.autonomous:
   assert after[:wire.MUTABLE_START]==second[:wire.MUTABLE_START] and after[wire.MUTABLE_END:]==second[wire.MUTABLE_END:]
   assert wire.response(before,second+self.original[len(second):])==wire.response(before,after+self.original[len(after):])
  else:assert after==second
  assert len(after) in (wire.bio.IMAGE_SIZE,524288)
  status,data=wire.response(before,after+self.original[len(after):])
  assert after[wire.bio.OFFSET:wire.bio.IMAGE_SIZE]==reply
  self.records.write(struct.pack('<QI',elapsed,len(incoming))+incoming+struct.pack('<I',len(data))+data)
  self.records.flush();self.timings.append(elapsed)
  if self.sequence==1 or self.sequence%32==0:
   with gzip.open(self.out/f'audit-{self.sequence:06d}.bin.gz','wb') as f:f.write(after)
   (self.out/f'audit-{self.sequence:06d}.txt').write_text(self.debugfs.joinpath('result.txt').read_text())
  assert status==0,f'RIO status {status}'
  return data
 def close(self):
  if self.fd is not None:
   fd,self.fd=self.fd,None;os.close(fd)
   capture(self.out/'close',self.debugfs);verify_close(self.out/'close')
   if self.autonomous and self.sequence:assert 'AUTONOMOUS STOP verified before any RAM restoration' in (self.out/'close/result.txt').read_text()
   subprocess.run(['rmmod',self.module_name],check=True)
  if self.records:self.records.close()
  if self.lock:self.lock.close()
  summary=dict(steps=self.sequence,restored=True,unloaded=True,driver_bound=Path('/sys/bus/pci/devices',self.bdf,'driver').exists(),latency_ms=dict(min=min(self.timings,default=0)/1e6,max=max(self.timings,default=0)/1e6,mean=sum(self.timings)/max(1,len(self.timings))/1e6))
  (self.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
  return summary

def main():
 p=argparse.ArgumentParser();p.add_argument('--bdf',required=True);p.add_argument('--payload',type=Path,required=True);p.add_argument('--module',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--steps',type=int,default=3);a=p.parse_args()
 board=Board(a.payload,a.module,a.output,bdf=a.bdf)
 try:
  for i in range(a.steps):
   msg=('RTEMS callback %d'%i).encode();req=struct.pack('<4I',0x314d5452,1,10,len(msg))+msg
   result=board.step(req);assert result==struct.pack('<5I',0x314d5452,i+1,i+1,i+1,len(msg))+msg,result.hex()
   if (i+1)%100==0:print('verified',i+1,flush=True)
 finally:print(json.dumps(board.close()))
if __name__=='__main__':main()
