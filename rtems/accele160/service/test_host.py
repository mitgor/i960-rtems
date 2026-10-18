#!/usr/bin/env python3
import socket,struct,tempfile,time
from pathlib import Path
from host import Service,ADDRESS,MAGIC
with tempfile.TemporaryDirectory() as d:
    page=bytearray(4096);writes=[]
    def write(addr,off,data):
        assert addr==ADDRESS;page[off:off+len(data)]=data;writes.append((off,data))
    def snap(addr):
        assert addr==ADDRESS
        w=struct.unpack_from('<16I',page)
        text=b'card reply\n'
        struct.pack_into('<9I',page,64,w[0],0,w[2],len(text),10,1,0,w[0],MAGIC)
        page[128:128+len(text)]=text
        return bytes(page)
    svc=Service(Path(d)/'socket',Path(d)/'log');svc.initialize(write)
    def connect(data):
        c=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);c.connect(str(svc.path));c.sendall(data);c.setblocking(False);return c
    a=connect(b'uptime\n');b=connect(b'bad\n');c=connect(b'x'*129+b'\n')
    for _ in range(8):svc.pump(snap,write)
    assert a.recv(1024)==b'card reply\n'
    assert b'unknown' in b.recv(1024);assert b'too long' in c.recv(1024);assert c.recv(1024)==b''
    for x in (a,b,c):x.close()
    n=len(writes);x=connect(b'partial');svc.pump(snap,write);x.close();svc.pump(snap,write);assert len(writes)==n
    clients=[]
    for _ in range(12):
        clients.append(connect(b''));svc.pump(snap,write)
    svc.pump(snap,write);svc.pump(snap,write);assert len(svc.clients)<=8
    for x in clients:x.close()
    svc.pump(snap,write)
    a=connect(b'version\n')
    for _ in range(6):svc.pump(snap,write)
    assert a.recv(1024)==b'card reply\n';a.close()
    # Invalid card length quarantines this endpoint; no retry/write follows.
    def bad(addr):
        data=bytearray(snap(addr));struct.pack_into('<I',data,76,769);return data
    a=connect(b'version\n')
    for _ in range(5):svc.pump(bad,write)
    assert svc.disabled and b'quarantined' in a.recv(1024);a.close()
    svc.close();assert not (Path(d)/'socket').exists()
    late=Service(Path(d)/'late',Path(d)/'late-log',defer=True)
    assert not late.path.exists();late.start();assert late.path.exists()
    # Timed-out card command is never retried; ownership remains with caller.
    c=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);c.connect(str(late.path));c.sendall(b'uptime\n')
    late.pump(snap,write);client,seq,start=late.pending;late.pending=(client,seq,start-6)
    def absent(addr):return bytes(4096)
    before=len(writes);late.pump(absent,write);assert late.disabled and not late.pending and len(writes)==before
    c.close();late.close()
print('host: valid, malformed, oversized, partial disconnect, queue bound, reconnect, corrupt reply PASS')
