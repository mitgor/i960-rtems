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
    if mode==3:
        w[144:150]=[0xc00521b0,0xc0001000,2,1,0xc0711000,0xc0711100]
        w[33]=0xc0779040;w[34]=w[149];w[80:144]=[w[148],0]*32
        if terminal:w[160]=1;w[163]=0x50001;w[164]=0xc0711200
    return struct.pack('<1024I',*w)

for mode in (1,2,3):
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
                assert len(writes)==3 and result['hardware_fault_tested']==(mode==3)
print('terminal capture, stale request, STOP retention and tamper tests passed')

for terminal in (False,True):
    b=page(3,terminal)
    for index in (33,34,144,145,146,147,148,149)+tuple(range(80,144))+((160,163,164) if terminal else ()):
        w=list(struct.unpack('<1024I',b));w[index]^=0x8000 if index==163 else 0x80000000
        try:host.validate(struct.pack('<1024I',*w),123,3,terminal)
        except AssertionError:pass
        else:raise AssertionError(('ownership tamper accepted',index))
print('owned-vector and real fault-record host validation passed')

# NMI path: host/local alias disagreement must prevent the PCI write.
for mismatch in (False,True):
    w=list(struct.unpack('<1024I',page(3)));w[25]=4
    w[151:155]=[0,0,0,0x7f]
    state=[struct.pack('<1024I',*w)];calls=[];mask=[0x7f]
    def nmi_write(addr,offset,data):
        if addr==host.ADDRESS and struct.unpack('<3I',data)==(123,1,0x54455354):
            v=list(struct.unpack('<1024I',state[0]));v[155]=1
            state[0]=struct.pack('<1024I',*v);mask[0]&=~8
    def inject():
        calls.append(1);v=list(struct.unpack('<1024I',state[0]))
        v[31]=host.DONE;v[20]=0x7d004;v[24]=v[28]=1;v[44]=125000
        v[151:155]=[0x100,8,0x80000000,0x77];v[160]=2;v[163]=248
        state[0]=struct.pack('<1024I',*v)
    with tempfile.TemporaryDirectory() as d:
        try:
            r=host.exercise(lambda _:state[0],nmi_write,123,4,d,
                lambda:dict(done='0'),lambda:dict(guard_changes='0'),
                nmi=inject,mu_read=lambda:(int(mismatch),0,mask[0]))
        except AssertionError:assert mismatch and not calls
        else:assert not mismatch and calls==[1] and r['nmi_hardware_tested']
print('NMI owner-only one-write gate and alias mismatch rejection passed (simulated)')

# Runtime profile: no terminal entry, exact acknowledged ownership sample.
w=list(struct.unpack('<1024I',page(3)));w[25]=5;w[166:172]=[2,42,12,0,1,0]
b=struct.pack('<1024I',*w);host.validate_runtime(b,123,2,0)
for index in (24,155,160,166,169,170,171):
    bad=w[:];bad[index]^=1
    try:host.validate_runtime(struct.pack('<1024I',*bad),123,2,0)
    except AssertionError:pass
    else:raise AssertionError(('runtime tamper accepted',index))
print('runtime sample epoch/phase/ownership/terminal rejection passed')
