#!/usr/bin/env python3
"""Bounded HTTP/input acceptance while the 32-frame card owner is running."""
import hashlib,json,re,struct,time,urllib.request
from pathlib import Path

base='http://127.0.0.1:8087'
out=Path(__import__('sys').argv[1]);out.mkdir(parents=True,exist_ok=False)
deadline=time.monotonic()+900
def get(path):
    with urllib.request.urlopen(base+path,timeout=5) as r:return r.read()
def post(path,token,obj):
    req=urllib.request.Request(base+path,json.dumps(obj).encode(),
        {'Content-Type':'application/json','X-Session-Token':token},method='POST')
    with urllib.request.urlopen(req,timeout=5) as r:return r.read()
while True:
    try:page=get('/').decode();break
    except Exception:
        if time.monotonic()>deadline:raise TimeoutError('browser did not start')
        time.sleep(.5)
token=re.search(r"const token='([0-9a-f]+)'",page).group(1)
def record(name,obj):(out/name).write_text(json.dumps(obj,indent=2)+'\n')
seen={};sent_down=False;sent_up=False
no_input=True
while time.monotonic()<deadline:
    try:status=json.loads(get('/status'))
    except Exception:break
    if status['frame']:
        frame=get('/frame.bin?v='+status['frame'])
        header=struct.unpack_from('<8I',frame)
        assert len(frame)==65568 and header[0:2]==(0x31424644,1)
        assert header[4:8]==(320,200,65536,0)
        gen=header[3]
        if gen not in seen:
            seen[gen]={'generation':gen,'sha256':hashlib.sha256(frame[32:]).hexdigest(),
                       'bytes':len(frame),'epoch':header[2],
                       'received_monotonic_ns':time.monotonic_ns()}
            (out/f'http-frame-{gen:04d}.bin').write_bytes(frame)
            record('status.json',status)
        if gen>=1 and not sent_down and not no_input:
            post('/key',token,{'key':173,'down':1});sent_down=True
        if gen>=4 and sent_down and not sent_up:
            post('/key',token,{'key':173,'down':0});sent_up=True
        if gen>=32:break
    time.sleep(.1)
record('result.json',{'frames':list(seen.values()),'key_down':sent_down,
                      'key_up':sent_up,'last_status':status})
print(f'HTTP captured {len(seen)} generations; key down/up {sent_down}/{sent_up}')
