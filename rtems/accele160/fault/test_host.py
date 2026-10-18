#!/usr/bin/env python3
"""Native negative tests of the real capture/retention gate; no hardware claim."""
import json,struct,tempfile
from pathlib import Path
import host

def page(mode,terminal=False):
    w=[0]*1024;w[16:19]=[host.MAGIC,123,1];w[25]=mode
    w[26]=int(not (mode==2 and terminal));w[31]=host.DONE if terminal else host.READY
    w[32]=0xfeffdd20;w[64]=0xc0000800
    if terminal:w[20]=0x7d000+mode;w[24]=w[28]=1;w[44]=125000;w[45]=65432
    return struct.pack('<1024I',*w)

for mode in (1,2):
    for terminal in (False,True):
        b=page(mode,terminal);host.validate(b,123,mode,terminal)
        for index in (16,17,18,25,26,31,32,64)+((20,24,28,38,48,49,50,51,52,53,54,55,56) if terminal else ()):
            w=list(struct.unpack('<1024I',b));w[index]^=1
            try:host.validate(struct.pack('<1024I',*w),123,mode,terminal)
            except AssertionError:pass
            else:raise AssertionError(('tamper accepted',index))
    for done,guard in (('0','0'),('1','0'),('0','1')):
        state=[page(mode)];writes=[]
        def write(addr,offset,data):
            writes.append((addr,offset,data))
            if addr==host.ADDRESS and struct.unpack('<3I',data)==(123,1,0x54455354):state[0]=page(mode,True)
        with tempfile.TemporaryDirectory() as d:
            try:
                result=host.exercise(lambda _:state[0],write,123,mode,d,
                    lambda:dict(done=done),lambda:dict(guard_changes=guard))
            except AssertionError:assert (done,guard)!=('0','0')
            else:
                assert (done,guard)==('0','0') and result['retained']
                assert len(writes)==3 and not result['hardware_fault_tested']
print('terminal capture, stale request, STOP retention and tamper tests passed')
