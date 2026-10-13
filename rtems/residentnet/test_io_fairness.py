#!/usr/bin/env python3
"""Execute the real snapshot reader against independently frozen controls and a
pending WAD service. Old page-wide locking is the negative baseline."""
import ast,threading,time
from pathlib import Path
r=Path(__file__).resolve().parent
node=next(n for n in ast.walk(ast.parse((r/'live.py').read_text())) if isinstance(n,ast.FunctionDef) and n.name=='frozen_page')
gate=threading.RLock();pending=threading.Event();served=threading.Event();frozen=[];generation=0;reads=[];latency=[]
def control(op,arg=0):
 global frozen,generation
 if op==7:generation+=1;frozen=[generation*1000+i for i in range(64)];return [0]*8
 assert op==5;time.sleep(.002)
 if arg==0:pending.set()
 reads.append(arg);return [0,0,frozen[arg],0,0,0,0,0]
def service():
 assert pending.wait(2);start=time.monotonic()
 with gate:latency.append(time.monotonic()-start);served.set()
ns=dict(io_gate=gate,control=control,time=time,pump_packets=lambda:None);exec(compile(ast.Module(body=[node],type_ignores=[]),str(r/'live.py'),'exec'),ns)
for page in range(3):
 pending.clear();served.clear();reads.clear();worker=threading.Thread(target=service);worker.start();out=ns['frozen_page'](page);worker.join(2);assert not worker.is_alive() and served.is_set();assert out==[generation*1000+i for i in range(64)] and reads==list(range(64));assert latency[-1]<.1,latency
pending.clear();served.clear();worker=threading.Thread(target=service);worker.start()
with gate:
 control(7)
 old=[control(5,i)[2] for i in range(64)]
 assert not served.is_set() # unchanged old locking really starves this service
worker.join(2);assert latency[-1]>.1,latency
print('PASS: actual frozen-page reader preserves all 64 words and services WAD between short groups; old page-wide lock fails service budget')
