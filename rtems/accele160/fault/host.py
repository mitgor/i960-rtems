"""Owner-thread software terminal gate; never opens a second PCI mapping."""
import json,secrets,struct,time
from pathlib import Path
ADDRESS=0xc0776000 # odd aperture -> record page c0777000
MAGIC=0x31544641
READY=0x59444152
DONE=0x454e4f44

def dma_fnv(data):
    h=2166136261
    for b in data:h=((h^b)*16777619)&0xffffffff
    return h

def dma_descriptors(w):
    return b''.join(struct.pack('<8I',w[180]+(i+1)*32 if i<1024 else 0,
        w[182]+(0 if i<1024 else 65536),0,w[181] if i<1024 else w[185],
        65536 if i<1024 else 32,7,0,0) for i in range(1025))

def validate_dma_observation(w):
    assert w[29]==0
    if w[25]>=8:
        assert w[175]==10000000 and w[195]==1 and w[203]==4096
        assert 4096<=w[202]<=100000
        assert w[196]==0x400 and w[197]==0 and w[201]==7
        assert w[180]<=w[198]<w[180]+32768 and w[198]%32==0
        assert w[199]==w[198]+32 and 0<w[200]<=65536
        assert w[176:180]==(0x400,0,w[199],w[200])
        assert w[186:192]==w[196:202] # still stalled after the full bound
    else:
        assert w[175]<10000000 and not w[186]&0x42d
        assert w[187:192]==(1,w[180]+32768,0,0,7)

    if w[25] in (10,11):
        assert w[208:210]==(3,0x400) and w[210]<10000000
        assert w[211:217]==(0,1,w[180]+32768,0,0,7)
        assert w[204]==w[192]==w[217] and w[205]==w[193]==w[218]
        assert w[219:221]==(1,1)

    if w[25] in (11,13):
        assert w[151]==0x100 and w[155]==1 and w[160]==2 and w[163]==248
        assert w[152]&8 and w[153]&0x80000000 and not w[154]&8
        assert w[221:224]==(w[152]&~8,w[153]&~0x80000000,w[154]|8)

    if w[25] in (12,13):
        assert w[208:221]==(1,)+(0,)*12
        assert w[204]==w[192]==w[235] and w[205]==w[193]==w[236]
        if w[25]==12:
            assert w[221:224]==(0,0,0)
            assert w[224]==w[204] and w[225]==w[224]^1
        else:
            assert w[224]==w[151]==0x100 and w[225]==0 and w[239]==151
        assert w[226:229]==(1,1,10000000)
        assert w[229:235]==w[186:192] and w[237:239]==(1,1)

def validate_dma_frame(data,slot,stalled):
    assert len(data)==77824 and data[:4096]==bytes([0xa5])*4096
    assert data[69664:]==bytes([0xa5])*8160
    expected=bytes((i^(i>>8)^0x69)&255 for i in range(65536))
    payload=data[4096:69632]
    if slot==1:assert payload==bytes([0x5a])*65536
    elif stalled:
        # A suspended write may finish queued PCI data. Accept only an exact
        # source prefix followed by the untouched initialization pattern.
        cut=next((i for i,(a,b) in enumerate(zip(payload,expected)) if a!=b),65536)
        assert payload[cut:]==bytes([0x5a])*(65536-cut)
    else:assert payload==expected
    assert data[69632:69664]==(struct.pack('<8I',*(0x444d4100+i for i in range(8))) if slot==0 and not stalled else bytes(32))

def initialize(write):
    nonce=secrets.randbelow(0xfffffffe)+1
    write(ADDRESS,0,struct.pack('<16I',nonce,*([0]*15)))
    return nonce

def decode(page):
    assert len(page)==4096
    return struct.unpack_from('<240I',page)

def validate(page,nonce,mode,terminal):
    w=decode(page)
    assert w[16:19]==(MAGIC,nonce,1) and w[25]==mode
    assert w[31]==(DONE if terminal else READY)
    assert w[32]==0xfeffdd20 and w[64]==0xc0000800
    assert w[26]==(0 if terminal and mode==2 else 1)
    if mode>=3:
        assert w[144:148]==(0xc00521b0,0xc0001000,2,1)
        assert 0xc0710000<=w[148]<0xc0724000 and w[148]%16==0
        assert 0xc0710000<=w[149]<0xc0724000 and w[149]%4==0
        assert w[33]==0xc0779040 and w[34]==w[149]
        assert w[80:144]==(w[148],0)*32
        if terminal:
            if mode in (3,6,8,10,12):
                assert w[160]==1 and w[163]&0xffffff==0x00050001
                assert 0xc0710000<=w[164]<0xc0724000
            else:
                assert w[160]==2 and w[155]==1
                assert w[151]&0x100 and w[152]&8 and w[153]&0x80000000
                assert not w[154]&8
                assert w[163]==248 # architectural interrupt procedure number
    if terminal:
        assert w[20]==0x7d000+((3 if mode%2==0 else 4) if mode>=6 else mode) and w[24]==1 and w[28]==1
        assert w[38]==0 and w[44]==125000 and w[45]<=125000
        if mode<6:assert w[48:57]==(0,)*9
        else:
            assert w[51:57]==(0,)*6
            assert w[176]&0x400 and not w[176]&0x2d
            assert w[177]==(0 if mode>=8 else 1) and w[183]==1024 and w[184]&0x400
            assert not w[184]&0x2d
            assert w[180]==w[181]+65536 and 0xc0800000<=w[181]<0xc0ff0000-98336
            assert w[180]%32==0 and w[182]%4096==0
            assert w[178]==0 or (w[180]<=w[178]<=w[180]+32768 and w[178]%32==0)
            assert w[179]<=65536
    return w

def exercise(snap,write,nonce,mode,out,status,pin_status,nmi=None,mu_read=None,frame_read=None,deny_release=None):
    assert mode in (1,2,3,4,6,7,8,9,10,11,12,13)
    out=Path(out);out.mkdir(exist_ok=True)
    pin_before=pin_status()
    assert pin_before.get('guard_changes')=='0' and status().get('done')=='0'
    before=snap(ADDRESS);validate(before,nonce,mode,False)
    (out/'ready.bin').write_bytes(before)
    # A stale nonce cannot trigger containment or alter the terminal record.
    write(ADDRESS,0,struct.pack('<3I',nonce^1,1,0x54455354))
    time.sleep(.1)
    stale=snap(ADDRESS);assert stale[64:]==before[64:]
    (out/'stale.bin').write_bytes(stale)
    if mode in (4,7,9,11,13):
        assert nmi is not None and mu_read is not None
        # Manual 273353 section 16.2: BAR0 first page maps MU registers.
        # Verify host/local IDR, IISR and IIMR aliases before the sole write.
        assert mu_read()==(decode(before)[153],decode(before)[152],decode(before)[154])
    triggered=time.monotonic()
    write(ADDRESS,0,struct.pack('<3I',nonce,1,0x54455354))
    if mode in (4,7,9,11,13):
        armed_deadline=time.monotonic()+5
        while time.monotonic()<armed_deadline:
            armed=snap(ADDRESS);aw=decode(armed)
            if aw[155]==1:break
            time.sleep(.01)
        else:raise RuntimeError('NMI arm deadline; retain all resources')
        validate(armed,nonce,mode,False)
        assert not mu_read()[0]&0x80000000 and not mu_read()[1]&8
        assert mu_read()[2]==(aw[154]&~8)
        (out/'armed.bin').write_bytes(armed)
        nmi() # Exactly one host PCI doorbell write, never sysctl or direct call.
    end=time.monotonic()+(30 if mode>=6 else 5)
    while time.monotonic()<end:
        page=snap(ADDRESS)
        if decode(page)[31]==DONE:break
        time.sleep(.01)
    else:raise RuntimeError('terminal record deadline; retain all resources')
    terminal_seconds=time.monotonic()-triggered
    (out/'terminal.bin').write_bytes(page);w=validate(page,nonce,mode,True)
    if mode in (11,13):
        # Independently read the PCI-visible MU aliases after the core's ack.
        mu=mu_read();(out/'mu-after.json').write_text(json.dumps(dict(idr=mu[0],iisr=mu[1],iimr=mu[2]),indent=2)+'\n')
        assert mu==(w[222],w[221],w[223])
    time.sleep(.1)
    again=snap(ADDRESS);assert again==page
    (out/'stable.bin').write_bytes(again)
    # Existing STOP cannot turn a terminal park into completion or release.
    write(0xc000e000,0xa4c,struct.pack('<I',0x504f5453));time.sleep(.1)
    stopped=snap(ADDRESS);assert stopped==page
    (out/'after-stop.bin').write_bytes(stopped)
    state=status();pin=pin_status()
    assert state.get('done')=='0' and pin.get('guard_changes')=='0' and pin==pin_before
    result=dict(schema=1,terminal_seconds=terminal_seconds,nonce=nonce,mode=mode,stable=True,retained=True,
        admission=state,pin=pin,code=w[20],ticks=w[27],hardware_fault_tested=mode in (3,6,8,10,12),nmi_hardware_tested=mode in (4,7,9,11,13),
        nmi_owned=mode>=3,scsi_excluded=False)
    if mode>=6:
        assert frame_read and deny_release
        validate_dma_observation(w)
        assert state.get('released')=='0'
        expected=bytes((i^(i>>8)^0x69)&255 for i in range(65536))
        for slot in (0,1):
            data=frame_read(slot);(out/f'frame{slot}.bin').write_bytes(data)
            validate_dma_frame(data,slot,mode in (8,9,12,13))
            if mode>=8:
                time.sleep(1)
                delayed=frame_read(slot);(out/f'delayed-frame{slot}.bin').write_bytes(delayed)
                assert delayed==data
        # Only odd 4 KiB pages are visible in the existing PCI aperture.
        # Full post-drain FNVs are computed on-card; host independently checks
        # every visible source/descriptor page and the complete DMA payload.
        assert w[192]==dma_fnv(expected) and w[194]==1
        descriptors=dma_descriptors(w);assert w[193]==dma_fnv(descriptors)
        for off in range(0,65536,8192):
            data=snap(w[181]-4096+off)
            (out/f'source-{off:05x}.bin').write_bytes(data)
            assert data==expected[off:off+4096]
        for off in range(0,32800,8192):
            data=snap(w[180]-4096+off)
            (out/f'descriptors-{off:05x}.bin').write_bytes(data)
            n=min(4096,32800-off);assert data[:n]==descriptors[off:off+n]
        denied=deny_release();(out/'release-denied.json').write_text(json.dumps(denied,indent=2)+'\n')
        assert denied['returncode']!=0 and pin_status()==pin_before and status().get('done')=='0'
        assert snap(ADDRESS)==page
        result.update(active_dma_at_entry=True,finite_bytes=1024*65536,drained_after_terminal=mode<8 or mode in (10,11),stalled_timeout=mode>=8,resumed_after_timeout=mode in (10,11),resume_refused=mode in (12,13),
            dma_source_retained=True,dma_destination_retained=True,completion_not_synthesized=True)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def validate_runtime(page,nonce,seq,phase,mode=5):
    assert mode in (5,14)
    w=validate(page,nonce,mode,False)
    assert w[24]==0 and w[160]==0 and w[155]==0
    assert w[166]==seq and w[167]>=6 and w[168]>=2
    assert w[169:172]==(0,1,phase)
    return w

def runtime_sample(snap,write,nonce,seq,out,phase=0,mode=5):
    out=Path(out)
    if not phase:write(ADDRESS,12,struct.pack('<2I',nonce,seq))
    deadline=time.monotonic()+5
    while True:
        page=snap(ADDRESS);w=decode(page)
        if w[166]==seq and w[171]==phase:break
        if time.monotonic()>deadline:
            out.write_bytes(page)
            raise RuntimeError('owned runtime sample deadline; retain resources')
        time.sleep(.01)
    out.write_bytes(page)
    validate_runtime(page,nonce,seq,phase,mode)
    # No second sample request, so the card-owned report must stay immutable.
    assert snap(ADDRESS)[64:]==page[64:]
    if mode==14:
        from importlib.util import spec_from_file_location,module_from_spec
        spec=spec_from_file_location('engine_inventory',Path(__file__).parent.parent/'ownership/inventory.py')
        module=module_from_spec(spec);spec.loader.exec_module(module)
        module.decode(page,nonce,seq,phase)
    return dict(sequence=seq,phase=phase,ticks=w[167],handoffs=w[168],owned=True)
