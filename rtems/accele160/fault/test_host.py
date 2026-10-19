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

# Active DMA requires the hardware Channel Active flag at terminal entry,
# not merely CCR enable, a queued descriptor, or a software pending flag.
for mode in (6,7):
    w=list(struct.unpack('<1024I',page(3,True)));w[25]=mode
    w[176:186]=[0x400,1,0xc0820020,65536,0xc0820000,0xc0810000,0x10000000,1024,0x400,0xc0712000]
    if mode==7:
        w[20]=0x7d004;w[160]=2;w[163]=248;w[155]=1
        w[151:155]=[0x100,8,0x80000000,0x77]
    host.validate(struct.pack('<1024I',*w),123,mode,True)
    for index,value in ((176,0),(176,0x408),(177,0),(183,0),(184,0),(180,0),(179,65537),(51,1)):
        bad=w[:];bad[index]=value
        try:host.validate(struct.pack('<1024I',*bad),123,mode,True)
        except AssertionError:pass
        else:raise AssertionError(('active DMA evidence tamper accepted',mode,index))
print('active DMA entry evidence rejects inactive, errors, invalid chain and peer activity')

# A disabled channel is NOT drained: require active CSR and frozen outstanding
# descriptor/count across entry and the entire timeout, with no completion marker.
w=[0]*208;w[25]=8;w[175]=10000000;w[180]=0xc0821000
w[195:204]=[1,0x400,0,0xc0821000,0xc0821020,50000,7,4097,4096]
w[176:180]=[0x400,0,w[199],w[200]];w[186:192]=w[196:202]
host.validate_dma_observation(tuple(w))
for index in (175,176,177,178,179,186,187,188,189,190,191,195,196,197,198,199,200,201,203):
    bad=w[:];bad[index]^=1
    try:host.validate_dma_observation(tuple(bad))
    except AssertionError:pass
    else:raise AssertionError(('stall evidence tamper accepted',index))
payload=bytes((i^(i>>8)^0x69)&255 for i in range(65536))
b=b'\xa5'*4096+payload[:4096]+b'\x5a'*(65536-4096)+bytes(32)+b'\xa5'*8160
host.validate_dma_frame(b,0,True)
for offset in (0,4100,69632,77823):
    bad=bytearray(b);bad[offset]^=1
    try:host.validate_dma_frame(bad,0,True)
    except AssertionError:pass
    else:raise AssertionError(('stall payload tamper accepted',offset))
print('stalled DMA: disabled is not drained; progress/error/marker/guard corruption rejected')

# The successful resumed transfer must retain a distinct timeout record.
w=w+[0]*16;w[25]=10;w[208:221]=[3,0x400,123,0,1,w[180]+32768,0,0,7,0,0,1,1]
host.validate_dma_observation(tuple(w))
for index in (175,186,187,204,205,208,209,211,212,213,214,215,216,217,218,219,220):
    bad=w[:];bad[index]^=1
    try:host.validate_dma_observation(tuple(bad))
    except AssertionError:pass
    else:raise AssertionError(('resume evidence tamper accepted',index))
bad=w[:];bad[210]=10000000
try:host.validate_dma_observation(tuple(bad))
except AssertionError:pass
else:raise AssertionError('resume timeout accepted as completion')
print('resume: distinct timeout/completion, fingerprints and guard evidence required')

# NMI resume additionally requires actual vector/source and acknowledged MU.
w[25]=11;w[151:156]=[0x100,0xb,0x80000000,0x73,1]
w[160]=2;w[163]=248;w[221:224]=[3,0,0x7b]
host.validate_dma_observation(tuple(w))
for index,mask in ((151,1),(152,8),(153,0x80000000),(154,8),(155,1),(160,1),(163,1),(221,8),(222,0x80000000),(223,8)):
    bad=w[:];bad[index]^=mask
    try:host.validate_dma_observation(tuple(bad))
    except AssertionError:pass
    else:raise AssertionError(('NMI resume evidence tamper accepted',index))
print('NMI resume: vector, source, arm, acknowledgement and mask required')

# Refusal preserves both exhausted bounds and rejects a corrected retry.
w=w+[0]*16;w[25]=12;w[208:224]=[1]+[0]*15
w[224]=w[204]=w[192]=w[235]=0x1234;w[225]=0x1235
w[205]=w[193]=w[236]=0x5678;w[226:229]=[1,1,10000000]
w[229:235]=w[186:192];w[237:239]=[1,1]
host.validate_dma_observation(tuple(w))
for index in tuple(range(208,239)):
    bad=w[:];bad[index]^=1
    try:host.validate_dma_observation(tuple(bad))
    except AssertionError:pass
    else:raise AssertionError(('refusal evidence tamper accepted',index))
print('refusal: no enable/completion, original evidence restored, retry latched, second timeout required')

# NMI refusal modifies only saved NISR evidence, with actual MU acknowledged.
w[25]=13;w[151:156]=[0x100,0xb,0x80000000,0x73,1];w[160]=2;w[163]=248
w[221:226]=[3,0,0x7b,0x100,0];w[239]=151
host.validate_dma_observation(tuple(w))
for index,mask in [(151,0x100),(152,8),(153,0x80000000),(154,8),(155,1),(160,1),(163,1)]+[(i,1) for i in range(208,240)]:
    bad=w[:];bad[index]^=mask
    try:host.validate_dma_observation(tuple(bad))
    except AssertionError:pass
    else:raise AssertionError(('NMI refusal tamper accepted',index))
print('NMI refusal: source evidence restored, MU ack intact, retry latched and second timeout required')
