"""Host-owned reference protocol; frame bytes come from unchanged native ray.c."""
import struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from host import Native,request as ray_request
MAGIC=0x31514642;READY=0x59444152;SIZE=5120;OFFSET=0x60000

def request(op,epoch=1,slot=0,gen=0,keys=0):
 return struct.pack('<8I',MAGIC,op,epoch,slot,gen,0,0,0)+(ray_request(keys=keys) if op==1 else bytes(32))
def fnv(data):
 h=2166136261
 for b in data:h=((h^b)*16777619)&0xffffffff
 return h

def validate(data,epoch,gen,slot):
 if len(data)!=SIZE:raise ValueError('slot size')
 h=struct.unpack('<8I',data[:32])
 if h!=(MAGIC,epoch,gen,4864,READY,fnv(data[64:4928]),gen^0xffffffff,slot):raise ValueError('publication')
 if data[32:64]!=b'\xa5'*32 or data[4928:]!=b'\x5a'*192:raise ValueError('guard')
 return data[64:4928]

class Model:
 def __init__(self):
  self.ray=Native();self.epoch=self.last=self.mask=0;self.gen=[0,0];self.slots=[bytes(SIZE),bytes(SIZE)]
 def step(self,data,seq):
  w=struct.unpack('<16I',data);magic,op,epoch,slot,gen=w[:5];status=0
  if magic!=MAGIC or op>3 or slot>1 or not epoch or any(w[5:8]) or (op!=1 and any(w[8:])):status=1
  elif op==0:
   if slot or gen:status=1
   elif self.mask:status=3
   elif epoch<=self.epoch:status=2
   else:
    self.ray.step(ray_request(op=0,columns=0,pixels=0));self.epoch=epoch;self.last=self.mask=0;self.gen=[0,0];self.slots=[bytes(SIZE),bytes(SIZE)]
  elif epoch!=self.epoch:status=2
  elif op==1:
   if w[8]!=0x31594152 or w[9:11]!=(1,80) or w[11]>15 or w[12]!=1 or any(w[13:]):status=1
   elif self.last==0xffffffff or gen!=self.last+1:status=2
   elif self.mask&(1<<slot):status=3
   else:
    frame=self.ray.step(data[32:]);self.slots[slot]=struct.pack('<8I',MAGIC,epoch,gen,4864,READY,fnv(frame),gen^0xffffffff,slot)+b'\xa5'*32+frame+b'\x5a'*192
    self.last=gen;self.gen[slot]=gen;self.mask|=1<<slot
  elif op==2:
   if not self.mask&(1<<slot) or gen!=self.gen[slot]:status=2
   else:
    b=bytearray(self.slots[slot]);b[16:20]=bytes(4);self.slots[slot]=bytes(b);self.mask&=~(1<<slot)
  elif slot or gen:status=1
  return struct.pack('<16I',MAGIC,1,status,self.epoch,self.mask,self.last,*self.gen,4864 if self.mask&1 else 0,4864 if self.mask&2 else 0,seq,0,0,0,0,0)

def cases(frames=80,epoch=1):
 yield 'init',request(0,epoch=epoch)
 # Fill both slots and exercise delayed/out-of-order acknowledgements.
 yield 'publish',request(1,epoch=epoch,slot=0,gen=1)
 yield 'publish',request(1,epoch=epoch,slot=1,gen=2,keys=8)
 yield 'busy',request(1,epoch=epoch,slot=0,gen=3)
 yield 'busy-reset',request(0,epoch=epoch+1)
 yield 'stale-ack',request(2,epoch=epoch,slot=0,gen=99)
 yield 'wrong-epoch',request(2,epoch=epoch+1,slot=0,gen=1)
 yield 'stale-produce',request(1,epoch=epoch,slot=0,gen=2)
 yield 'query-full',request(3,epoch=epoch)
 yield 'ack',request(2,epoch=epoch,slot=1,gen=2)
 yield 'duplicate-ack',request(2,epoch=epoch,slot=1,gen=2)
 yield 'publish',request(1,epoch=epoch,slot=1,gen=3,keys=4)
 yield 'ack',request(2,epoch=epoch,slot=0,gen=1)
 yield 'ack',request(2,epoch=epoch,slot=1,gen=3)
 yield 'reset',request(0,epoch=epoch+1)
 yield 'old-epoch',request(1,epoch=epoch,slot=0,gen=4)
 for i in range(frames):
  yield 'steady-publish',request(1,epoch=epoch+1,slot=i%2,gen=i+1,keys=i//10%16)
  yield 'steady-ack',request(2,epoch=epoch+1,slot=i%2,gen=i+1)
 yield 'query-empty',request(3,epoch=epoch+1)
 yield 'close-unacked',request(1,epoch=epoch+1,slot=0,gen=frames+1,keys=8)
