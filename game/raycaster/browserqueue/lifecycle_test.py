#!/usr/bin/env python3
"""Bounded real-server lifecycle tests; select native or accepted card queue."""
import argparse
import http.client
import json
from pathlib import Path
import signal
import socket
import struct
import subprocess
import sys
import time
p=argparse.ArgumentParser()
p.add_argument('--backend',choices=['native','card-queue'],default='native')
p.add_argument('--payload',type=Path);p.add_argument('--module',type=Path)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--mode',choices=['idle','limit','signal','disconnect'],required=True)
p.add_argument('--queue-metadata',choices=['rewrite','journal'],default='rewrite')
a=p.parse_args()
if a.backend=="native" and a.mode in ("signal","disconnect"):
    p.error("controlled mid-transaction tests require the card intent log; native signal coverage is in test.py")
assert not a.output.exists()
with socket.socket() as sock:
    sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
args=[sys.executable,str(Path(__file__).resolve().parents[1]/'server.py'),'--backend',a.backend,'--queue-metadata',a.queue_metadata,'--port',str(port),'--output',str(a.output),'--idle-timeout','1' if a.mode=='idle' else '10','--max-frames','2' if a.mode=='limit' else '16']
if a.backend!='native':args+=['--payload',str(a.payload),'--module',str(a.module)]
proc=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
def fetch():
    c=http.client.HTTPConnection('127.0.0.1',port,timeout=10)
    c.request('POST','/step','{"keys":8}',{'Content-Type':'application/json'})
    r=c.getresponse();assert r.status==200;data=json.loads(r.read());c.close();return data
try:
    ready=proc.stdout.readline();assert 'http://127.0.0.1:' in ready,ready
    if a.mode=='limit':
        assert fetch()['frame_id']==1;assert fetch()['frame_id']==2
    elif a.mode in ('signal','disconnect'):
        assert fetch()['frame_id']==1
        c=socket.create_connection(('127.0.0.1',port),timeout=10)
        body=b'{"keys":8}'
        c.sendall(f'POST /step HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\n\r\n'.encode()+body)
        if a.backend=='card-queue':
            # Intent is written before execution; poll locally while the card
            # transaction runs. Do not issue another firmware command.
            deadline=time.monotonic()+5
            while True:
                try:
                    journal=a.output/'metadata-journal.jsonl'
                    if journal.exists():
                        count=sum(json.loads(line)[2].get('kind')=='intent' for line in journal.read_bytes().splitlines(keepends=True) if line.endswith(b'\n'))
                    else:count=len(json.loads((a.output/'browser-requests.json').read_text()))
                except json.JSONDecodeError:count=0
                if count==3:break
                assert time.monotonic()<deadline
                time.sleep(.0005)
        if a.mode=='signal':
            proc.send_signal(signal.SIGTERM)
            response=http.client.HTTPResponse(c);response.begin()
            assert response.status==200 and json.loads(response.read())['frame_id']==2
        else:
            c.setsockopt(socket.SOL_SOCKET,socket.SO_LINGER,struct.pack('ii',1,0))
        c.close()
    stdout,stderr=proc.communicate(timeout=20)
    session=json.loads((a.output/'browser-session.json').read_text())
    if a.mode=='disconnect':
        assert session['exit_reason'] in ('ConnectionResetError','BrokenPipeError'),session
        assert proc.returncode!=0
    else:
        assert proc.returncode==0,stderr
        assert session['exit_reason']=={'idle':'idle-timeout','limit':'frame-limit','signal':'signal'}[a.mode]
    if a.backend=='card-queue':
        summary=json.loads((a.output/'summary.json').read_text())
        assert summary['restored'] and summary['unloaded'] and not summary['driver_bound']
        assert summary['steps']==(1 if a.mode=='idle' else 3),summary
    (a.output/'server-stdout.txt').write_text(ready+stdout)
    (a.output/'server-stderr.txt').write_text(stderr)
    (a.output/'lifecycle-check.json').write_text(json.dumps(dict(mode=a.mode,returncode=proc.returncode,session=session),indent=2)+'\n')
    print(json.dumps(dict(mode=a.mode,returncode=proc.returncode,session=session)))
finally:
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
        proc.communicate(timeout=20)
