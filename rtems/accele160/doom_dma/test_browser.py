#!/usr/bin/env python3
"""Exercise the browser API and input bounds without a card session."""
import json,struct,urllib.request,time
from browser import BrowserSession
s=BrowserSession(0)
base=f'http://127.0.0.1:{s.port}'
def get(path):
    with urllib.request.urlopen(base+path,timeout=2) as r:return r.read()
def post(path,body):
    req=urllib.request.Request(base+path,json.dumps(body).encode(),
        {'X-Session-Token':s.token,'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=2) as r:return r.status
try:
    assert b'AcceleRAID 160' in get('/')
    assert json.loads(get('/status'))['frame']==''
    data=bytes(65536)
    s.publish(1,data)
    packet=get('/frame.bin?v=1')
    assert len(packet)==65568 and struct.unpack_from('<8I',packet)==(
        0x31424644,1,s.epoch,1,320,200,65536,0)
    assert packet[32:]==data
    assert post('/key',{'key':173,'down':1})==200
    assert s.next_key()==(173|0x100)
    assert post('/key',{'key':173,'down':0})==200
    assert s.next_key()==173
    assert not s.disconnected(60)
    s.client_seen=time.monotonic()-61
    assert s.disconnected(60)
    assert post('/heartbeat',{})==200 and not s.disconnected(60)
    assert post('/stop',{})==200 and s.stop.is_set()
    print('browser binary frame, keys, STOP and session identity: verified')
finally:s.close()
