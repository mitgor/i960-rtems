"""Independent combined request validation; original renderer stays the oracle."""
import struct,sys,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
spec=importlib.util.spec_from_file_location('fq_original_model',Path(__file__).resolve().parents[1]/'queue/model.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
Base=base.Model;MAGIC=base.MAGIC;request=base.request;ray_request=base.ray_request;old_cases=base.cases

def replace(epoch=1,slot=0,gen=2,ack=1,keys=0):
 return struct.pack('<8I',MAGIC,4,epoch,slot,gen,ack,0,0)+ray_request(keys=keys)

class Model(Base):
 def step(self,data,seq):
  w=struct.unpack('<16I',data)
  if w[1]!=4:return super().step(data,seq)
  magic,op,epoch,slot,gen,ack=w[:6];status=0
  if magic!=MAGIC or slot>1 or not epoch or any(w[6:8]):status=1
  elif epoch!=self.epoch:status=2
  elif w[8]!=0x31594152 or w[9:11]!=(1,80) or w[11]>15 or w[12]!=1 or any(w[13:]):status=1
  elif self.last==0xffffffff or gen!=self.last+1:status=2
  elif not self.mask&(1<<slot) or ack!=self.gen[slot]:status=2
  if not status:
   super().step(request(2,epoch,slot,ack),seq)
   return super().step(request(1,epoch,slot,gen,w[11]),seq)
  return struct.pack('<16I',MAGIC,1,status,self.epoch,self.mask,self.last,*self.gen,4864 if self.mask&1 else 0,4864 if self.mask&2 else 0,seq,0,0,0,0,0)

def cases(frames=80,epoch=1,combined=True):
 # The original ownership/error sequence; both slots are empty afterward.
 for label,data in old_cases(frames=0,epoch=epoch):
  if label in ('query-empty','close-unacked'):break
  yield label,data
 e=epoch+1
 if combined:
  yield 'empty-replace',replace(e)
  yield 'setup',request(1,e,0,1)
  yield 'setup',request(1,e,1,2,8)
  yield 'stale-combined-ack',replace(e,0,3,99)
  yield 'stale-combined-generation',replace(e,0,2,1)
  yield 'wrong-combined-epoch',replace(e+1,0,3,1)
  bad=bytearray(replace(e,0,3,1));struct.pack_into('<I',bad,40,79)
  yield 'malformed-combined-render',bytes(bad)
  bad=bytearray(replace(e,0,3,1));struct.pack_into('<I',bad,24,1)
  yield 'malformed-combined-reserved',bytes(bad)
  yield 'replace-full-second',replace(e,1,3,2,4)
  yield 'duplicate-combined',replace(e,1,3,2,4)
  yield 'replace-full-first',replace(e,0,4,1,8)
  yield 'stale-old-ack',request(2,e,0,1)
  yield 'drain',request(2,e,0,4)
  yield 'drain',request(2,e,1,3)
  yield 'empty-after-drain',replace(e,0,5,4)
 # Both variants start measured renders from the identical reset/seed state.
 yield 'steady-reset',request(0,e+1)
 yield 'seed',request(1,e+1,0,1)
 for i in range(frames):
  if combined:yield 'steady-combined',replace(e+1,0,i+2,i+1,i//10%16)
  else:
   yield 'steady-ack',request(2,e+1,0,i+1)
   yield 'steady-publish',request(1,e+1,0,i+2,i//10%16)
 yield 'query-unacked',request(3,e+1)
 # CLOSE must restore even when the last frame remains occupied.
