"""Independent diagnostic oracle and bounded two-slot stress sequences."""
import struct
from combined.model import Model as Base,request,replace,cases as combined_cases,MAGIC

def bench(epoch=1,slot=0,count=0,which=1):return struct.pack('<16I',MAGIC,5,epoch,slot,count,which,*([0]*10))
class Model(Base):
 def step(self,data,seq):
  w=struct.unpack('<16I',data)
  if w[1]!=5:return super().step(data,seq)
  magic,op,epoch,slot,count,which=w[:6];status=0
  if magic!=MAGIC or slot>1 or not epoch or any(w[6:]):status=1
  elif epoch!=self.epoch:status=2
  elif count>32 or which not in (1,2):status=1
  elif not self.mask&(1<<slot):status=2
  return struct.pack('<16I',MAGIC,1,status,self.epoch,self.mask,self.last,*self.gen,4864 if self.mask&1 else 0,4864 if self.mask&2 else 0,seq,0,0,0,0,0)

def cases(epoch=1,suite='combined'):
 if suite=='combined':yield from combined_cases(epoch=epoch);return
 if suite=='bench':
  yield 'init',request(0,epoch)
  yield 'bench-empty',bench(epoch)
  yield 'seed',request(1,epoch,0,1)
  yield 'bench-limit',bench(epoch,count=33)
  yield 'bench-selector',bench(epoch,which=3)
  yield 'bench-epoch',bench(epoch+1)
  bad=bytearray(bench(epoch));bad[24]=1;yield 'bench-reserved',bytes(bad)
  for repeat in range(5):
   for which in (1,2):
    counts=[0,32,1,16,4,8]
    for count in (counts if repeat%2==0 else counts[::-1]):yield f'bench-{which}-{count}',bench(epoch,count=count,which=which)
  return
 assert suite=='stress'
 for cycle in range(8):
  e=epoch+cycle
  yield 'reset',request(0,e)
  yield 'seed',request(1,e,0,1)
  yield 'seed',request(1,e,1,2,8)
  gens=[1,2];last=2
  for i in range(64):
   slot=(i//3)%2;last+=1;old=gens[slot]
   cmd=replace(e,slot,last,old,i%16)
   yield 'stress-replace',cmd;gens[slot]=last
   if i%8==0:
    yield 'stress-duplicate',cmd
    yield 'stress-old-ack',request(2,e,slot,old)
    yield 'stress-busy',request(1,e,1-slot,last+1)
    yield 'stress-busy-reset',request(0,e+1)
  if cycle!=7:
   yield 'drain',request(2,e,1,gens[1]);yield 'drain',request(2,e,0,gens[0])
 # Last cycle leaves BOTH slots occupied for complete CLOSE restoration.
