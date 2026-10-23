#!/usr/bin/env python3
"""Observe real browser packets, exercise held keys, request audited STOP."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import time
import urllib.request

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--url',default='http://192.168.2.80:8087')
p.add_argument('--out',type=Path,required=True)
p.add_argument('--frames',type=int,default=1024)
p.add_argument('--input',action='store_true')
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
start=time.monotonic();deadline=start+1200
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))

def get(path):
    with opener.open(a.url+path,timeout=5) as r:return r.read()

while True:
    try:page=get('/').decode();break
    except Exception:
        if time.monotonic()>deadline:raise TimeoutError('browser startup')
        time.sleep(.5)
token=re.search(r"const token='([0-9a-f]+)'",page).group(1)

def post(path,data):
    request=urllib.request.Request(a.url+path,json.dumps(data).encode(),
        {'Content-Type':'application/json','X-Session-Token':token})
    with opener.open(request,timeout=5) as r:return r.read()

seen={};events=[];last_heartbeat=0;first=None
for _ in range(1000000):
    if time.monotonic()>deadline:raise TimeoutError('frame deadline')
    if time.monotonic()-last_heartbeat>=1:
        post('/heartbeat',{});last_heartbeat=time.monotonic()
    status=json.loads(get('/status'))
    if status['frame']:
        packet=get('/frame.bin');header=struct.unpack_from('<8I',packet)
        assert len(packet)==65568 and header[:2]==(0x31424644,1)
        assert header[4:]==(320,200,65536,0)
        gen=header[3]
        if gen not in seen:
            if first is None:first=time.monotonic()
            seen[gen]=dict(generation=gen,sha256=hashlib.sha256(packet[32:]).hexdigest(),
                           observed_ns=time.monotonic_ns())
            if gen<=32 or gen%100==0:(a.out/f'frame-{gen:06d}.bin').write_bytes(packet)
            if gen%100==0:print('HTTP frame',gen,flush=True)
        if a.input:
            for threshold,key,down in ((100,173,1),(120,173,0),(140,163,1),(150,163,0)):
                event=(threshold,key,down)
                if gen>=threshold and event not in events:
                    post('/key',dict(key=key,down=down));events.append(event)
        if gen>=a.frames:
            post('/stop',{});break
    time.sleep(.015)
else:raise TimeoutError('probe loop')
rows=list(seen.values())
summary=dict(frames=rows,events=events,stop_posted=True,
             startup_seconds=first-start,elapsed_seconds=time.monotonic()-start,
             observer_fps=(len(rows)-1)*1e9/(rows[-1]['observed_ns']-rows[0]['observed_ns']))
(a.out/'result.json').write_text(json.dumps(summary,indent=2)+'\n')
print('HTTP/input/STOP probe complete:',len(seen),'frames',flush=True)
