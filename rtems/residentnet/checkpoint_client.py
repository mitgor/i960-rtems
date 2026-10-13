"""Read immutable startup checkpoints without claiming engine completion."""
import json,os,struct,time
def barrier_stage(stage):return stage in (42,43,44,50,51,63,80) or 81<=stage<=98
MAGIC=0x31504344
class Checkpoints:
 def __init__(self,u,barriers=False):self.u=u;self.rows=[];self.last=0;self.barriers=barriers
 def pump(self,force=False):
  if not force and time.monotonic()-self.last<.5:return
  self.last=time.monotonic()
  for _ in range(32):
   index=len(self.rows)+1;assert index<=512,'checkpoint capacity exhausted'
   w=list(struct.unpack('<8I',self.u.io(7,struct.pack('<I',index))))
   assert w[0]==MAGIC
   if not w[1]:
    assert w[2]==len(self.rows) and not any(w[3:]),'checkpoint loss/overflow';return
   assert w[1]==index and w[2] and 0<w[3]<=102
   self.rows.append(w)
   with (self.u.out/'startup-checkpoints.jsonl').open('a') as f:
    f.write(json.dumps(w)+'\n');f.flush()
    if self.barriers and barrier_stage(w[3]):os.fsync(f.fileno())
   if self.barriers and barrier_stage(w[3]):
    assert self.u.io(8,struct.pack('<2I',w[1],w[2]))==struct.pack('<2I',w[1],w[2])
  if force:self.pump(True)
