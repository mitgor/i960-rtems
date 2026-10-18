#!/usr/bin/env python3
"""Exercise the browser API and input bounds without a card session."""
import json,struct,urllib.request,urllib.error,time
from browser import BrowserSession
s=BrowserSession(0)
base=f'http://127.0.0.1:{s.port}'
def get(path):
    with urllib.request.urlopen(base+path,timeout=2) as r:return r.read()
def post(path,body):
    req=urllib.request.Request(base+path,json.dumps(dict(body,run_id=body.get('run_id',s.run_id))).encode(),
        {'X-Session-Token':s.token,'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=2) as r:return r.status
try:
    assert b'AcceleRAID 160' in get('/') and b'id="flat"' not in get('/')
    try:post('/key',dict(key=192,down=1));raise AssertionError('unsupported F6 accepted')
    except urllib.error.HTTPError as error:assert error.code==400
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
    s.idle(1)
    assert post('/restart',{})==200 and s.restart.is_set()
    s.begin_game(2)
    assert not s.stop.is_set() and not s.restart.is_set() and s.next_key() is None
    for path,body in (('/key',dict(key=173,down=1,run_id=1)),('/stop',dict(run_id=1)),('/restart',dict(run_id=1))):
        try:post(path,body);raise AssertionError('stale request accepted')
        except urllib.error.HTTPError as error:assert error.code==409
    assert not s.stop.is_set()
    s.publish(2,data)
    assert json.loads(get('/status'))['run_id']==2
    print('browser binary frame, keys, STOP and session identity: verified')
finally:s.close()

# Only flat-enabled engines expose F6; status follows validated frame telemetry.
s=BrowserSession(0,runtime_flat=True);base=f'http://127.0.0.1:{s.port}'
try:
    assert b'id="flat"' in get('/')
    post('/key',dict(key=192,down=1));post('/key',dict(key=192,down=1))
    assert s.next_key()==448 and s.next_key() is None
    post('/key',dict(key=192,down=0));assert s.next_key()==192
    s.publish(1,bytes(65536),dict(flat_planes=1,flat_switches=1))
    status=json.loads(get('/status'));assert status['flat_planes']==status['flat_switches']==1
    s.idle(1);s.begin_game(2);assert s.flat_mode==s.flat_switches==0
    print('flat F6, debounce, confirmed mode telemetry and fresh-game reset: verified')
finally:s.close()
