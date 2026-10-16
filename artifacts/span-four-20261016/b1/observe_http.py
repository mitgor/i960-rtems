#!/usr/bin/env python3
"""Read-only binary receiver; verifies embedded identity, exact size and palette."""
import hashlib,json,struct,time,urllib.request
from pathlib import Path
out=Path(__file__).with_name('http-observations.jsonl');last=None;deadline=time.monotonic()+3300;started=False
while time.monotonic()<deadline:
 try:
  with urllib.request.urlopen('http://192.168.2.75:8087/status',timeout=3) as r:s=json.load(r)
  started=True
  if s.get('frame') and s['frame']!=last:
   t=time.monotonic()
   with urllib.request.urlopen('http://192.168.2.75:8087/frame.bin?v='+s['frame'],timeout=3) as r:b=r.read()
   assert len(b)==65568;magic,version,session,g,w,h,n,crc=struct.unpack_from('<8I',b)
   assert (magic,version,w,h,n)==(0x31424644,1,320,200,65536) and crc in (0,1)
   name=f'{session}-{g}'
   if name!=last:
    row=dict(frame=name,received=time.monotonic(),fetch_seconds=time.monotonic()-t,sha256=hashlib.sha256(b).hexdigest(),payload_sha256=hashlib.sha256(b[32:]).hexdigest(),crc=bool(crc))
    with out.open('a') as f:f.write(json.dumps(row)+'\n')
    print(json.dumps(row),flush=True);last=name
 except (OSError,TimeoutError):
  if started and last:break
 time.sleep(.05)
