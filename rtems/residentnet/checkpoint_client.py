"""Read immutable startup checkpoints without claiming engine completion."""
import json,struct,time
MAGIC=0x31504344
class Checkpoints:
 def __init__(self,u):self.u=u;self.rows=[];self.last=0
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
   with (self.u.out/'startup-checkpoints.jsonl').open('a') as f:f.write(json.dumps(w)+'\n')
  if force:self.pump(True)
