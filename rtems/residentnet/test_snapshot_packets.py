#!/usr/bin/env python3
"""A slow full audit must forward TUN packets before a client times out."""
import ast
from pathlib import Path
from types import SimpleNamespace
p=Path(__file__).with_name('live.py')
node=next(n for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.FunctionDef) and n.name=='frozen_page')
class Gate:
 def __init__(self):self.held=False
 def __enter__(self):assert not self.held;self.held=True
 def __exit__(self,*unused):self.held=False
clock=[0.0];reads=[];forwarded=[];gate=Gate();generation=[0]
def control(op,arg=0):
 assert gate.held
 if op==7:generation[0]+=1;return [0]*8
 assert op==5;clock[0]+=.12;reads.append(arg)
 return [0,0,1000*generation[0]+arg,0,0,0,0,0]
def pump():
 assert not gate.held
 forwarded.append(clock[0])
ns=dict(io_gate=gate,control=control,pump_packets=pump,time=SimpleNamespace(sleep=lambda _:None))
exec(compile(ast.Module(body=[node],type_ignores=[]),str(p),'exec'),ns)
for page in range(3):
 start=clock[0];begin=len(forwarded);reads.clear()
 assert ns['frozen_page'](page)==[1000*(page+1)+i for i in range(64)]
 assert reads==list(range(64))
 times=[start]+forwarded[begin:];assert len(times)==17
 assert max(b-a for a,b in zip(times,times[1:]))<.481
 assert clock[0]-start>7.67 # old forwarding only after the page exceeds budget
print('PASS: three complete 64-word pages; packet forwarding gap <=480 ms under 120 ms/word audit; old page blocks 7.68 s')

# Execute the real packet pump with a pending RX rejected once, then accepted.
# A disabled pump must not issue parked/pre-start packet ioctls.
import errno,struct
from pump import send_pending
pump_node=next(n for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.FunctionDef) and n.name=='pump_packets')
wrapper=ast.parse('def make():\n pending_rx=None\n').body[0]
wrapper.body += [pump_node,ast.Return(value=ast.Name(id='pump_packets',ctx=ast.Load()))]
rx=b'\x45'+bytes(39);tx=bytearray(40);tx[0]=0x45;tx[9]=17
calls=[];written=[];rx_reads=[];attempt=[0]
def packet(op,data=b''):
 calls.append((op,data))
 if op==1:
  attempt[0]+=1
  if attempt[0]==1:raise BlockingIOError(errno.EAGAIN,'busy')
  assert data==rx
  return b''
 assert op==2
 return struct.pack('<I',len(tx))+tx
ns=dict(traffic_active=False,g=SimpleNamespace(fd=7),select=SimpleNamespace(select=lambda *args:([7],[],[])),os=SimpleNamespace(read=lambda fd,n:(rx_reads.append(fd) or rx),write=lambda fd,data:(written.append(bytes(data)) or len(data))),send_pending=send_pending,packet=packet,struct=struct,drop=set(),dropped=[],b=None)
exec(compile(ast.fix_missing_locations(ast.Module(body=[wrapper],type_ignores=[])),str(p),'exec'),ns)
f=ns['make']();f();assert not calls
ns['traffic_active']=True;f();f()
assert rx_reads==[7] and calls==[(1,rx),(2,b''),(1,rx),(2,b'')] and written==[bytes(tx)]*2
ns['traffic_active']=False;f();assert len(calls)==4
print('PASS actual packet pump preserves rejected RX, drains TX, and issues no ioctls when inactive')
