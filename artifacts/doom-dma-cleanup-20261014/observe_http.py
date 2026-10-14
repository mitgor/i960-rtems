#!/usr/bin/env python3
"""Read-only Mac observer of the same status/PNG endpoints used by the browser."""
import hashlib,json,time,urllib.request
from pathlib import Path
out=Path(__file__).with_name('diagnostic-http-observations.jsonl');last=None;deadline=time.monotonic()+3300;started=False
while time.monotonic()<deadline:
 try:
  with urllib.request.urlopen('http://192.168.2.75:8087/status',timeout=3) as r:s=json.load(r)
  started=True
  if s.get('frame') and s['frame']!=last:
   begin=time.monotonic()
   with urllib.request.urlopen('http://192.168.2.75:8087/frame.png?frame='+s['frame'],timeout=3) as r:data=r.read()
   row=dict(frame=s['frame'],received=time.monotonic(),fetch_seconds=time.monotonic()-begin,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
   with out.open('a') as f:f.write(json.dumps(row)+'\n')
   print(json.dumps(row),flush=True);last=s['frame']
 except Exception:
  if started and last:break
 time.sleep(.25)
