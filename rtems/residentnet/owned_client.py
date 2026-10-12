"""Independent invocation-scoped application cancellation, never a write retry."""
import errno,hashlib,json,struct,time,zlib
from pathlib import Path
MAGIC=0x3252444f
class Control:
 def __init__(self,u,stop):self.u=u;self.stop=stop;self.baseline=self.query();self.sent=False;self.records=[]
 def query(self):
  w=struct.unpack('<8I',self.u.io(5));assert w[0]==MAGIC;return w
 def request(self,generation,expected=0):
  try:self.u.io(6,struct.pack('<8I',MAGIC,generation,0,0,0,0,0,0))
  except OSError as e:
   assert e.errno==expected;return
  assert not expected
 def serve(self):
  w=self.query()
  if self.stop and not self.sent and w[2] and w[1]>self.baseline[1] and w[4]>=self.baseline[4]+16:
   # A different invocation ID must not cancel this one. Only the explicitly
   # accepted current generation is sent afterward; neither write is retried.
   self.request(w[1]+1,errno.ESTALE);self.request(w[1]);self.sent=True;self.records.append(dict(generation=w[1],snapshot=list(w)))
  return False

def exercise(u,root):
 root=Path(root);m=json.loads((root/'manifest.json').read_text());b=(root/'template.bin').read_bytes();assert hashlib.sha256(b).hexdigest()==m['sha256']
 control=Control(u,False);control.request(1,errno.ESTALE);u.command(16,expected=1)
 rows=[]
 # A CRC-valid changed program is still forbidden.
 bad=bytearray(b);bad[0]^=1
 def load(blob):
  u.begin([(s['offset'],s['file_bytes'],s['memory_bytes'],s['flags'],zlib.crc32(blob[s['offset']:s['offset']+s['file_bytes']])) for s in m['sections']],m['entry'])
  for i,s in enumerate(m['sections']):
   if s['file_bytes']:u.write(i,blob[s['offset']:s['offset']+s['file_bytes']])
  u.prepare()
 load(bad);u.command(16,expected=2);u.command(5)
 load(b);base=u.command(14)[5]
 for stop in (False,True,False):
  control=Control(u,stop);u.service=control.serve;start=time.monotonic()
  try:w=u.command(16,timeout=60)
  finally:u.service=None
  expected_code=53 if stop else 37;assert w[5]==MAGIC^0x49393630^expected_code and w[4]==3
  result=[u.command(17,i)[5] for i in range(8)]
  assert result[0:3]==[0x49393630^7,3,2] and result[5:]==[int(stop),expected_code,0]
  assert 0<=result[4]<=12000 and (stop or result[4]>=10000)
  final=control.query();assert final[2]==0 and final[3]==int(stop)
  control.request(final[1],errno.ESTALE)
  rows.append(dict(stop=stop,seconds=time.monotonic()-start,value=w[5],result=result,control=list(final),requests=control.records))
 u.command(5)
 (u.out/'owned-results.json').write_text(json.dumps(dict(manifest=m,base=0xc02d0040+base,runs=rows),indent=2)+'\n');(u.out/'owned-template.bin').write_bytes(b)
