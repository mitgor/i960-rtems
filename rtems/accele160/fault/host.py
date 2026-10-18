"""Owner-thread software terminal gate; never opens a second PCI mapping."""
import json,secrets,struct,time
from pathlib import Path
ADDRESS=0xc0776000 # odd aperture -> record page c0777000
MAGIC=0x31544641
READY=0x59444152
DONE=0x454e4f44

def initialize(write):
    nonce=secrets.randbelow(0xfffffffe)+1
    write(ADDRESS,0,struct.pack('<16I',nonce,*([0]*15)))
    return nonce

def decode(page):
    assert len(page)==4096
    return struct.unpack_from('<176I',page)

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
            if mode==3:
                assert w[160]==1 and w[163]&0xffffff==0x00050001
                assert 0xc0710000<=w[164]<0xc0724000
            else:
                assert w[160]==2 and w[155]==1
                assert w[151]&0x100 and w[152]&8 and w[153]&0x80000000
                assert not w[154]&8
                assert w[163]==248 # architectural interrupt procedure number
    if terminal:
        assert w[20]==0x7d000+mode and w[24]==1 and w[28]==1
        assert w[38]==0 and w[44]==125000 and w[45]<=125000
        assert w[48:57]==(0,)*9 # injections are before DMA initialization
    return w

def exercise(snap,write,nonce,mode,out,status,pin_status,nmi=None,mu_read=None):
    assert mode in (1,2,3,4)
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
    if mode==4:
        assert nmi is not None and mu_read is not None
        # Manual 273353 section 16.2: BAR0 first page maps MU registers.
        # Verify host/local IDR, IISR and IIMR aliases before the sole write.
        assert mu_read()==(decode(before)[153],decode(before)[152],decode(before)[154])
    write(ADDRESS,0,struct.pack('<3I',nonce,1,0x54455354))
    if mode==4:
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
    end=time.monotonic()+5
    while time.monotonic()<end:
        page=snap(ADDRESS)
        if decode(page)[31]==DONE:break
        time.sleep(.01)
    else:raise RuntimeError('terminal record deadline; retain all resources')
    w=validate(page,nonce,mode,True);(out/'terminal.bin').write_bytes(page)
    time.sleep(.1)
    again=snap(ADDRESS);assert again==page
    (out/'stable.bin').write_bytes(again)
    # Existing STOP cannot turn a terminal park into completion or release.
    write(0xc000e000,0xa4c,struct.pack('<I',0x504f5453));time.sleep(.1)
    stopped=snap(ADDRESS);assert stopped==page
    (out/'after-stop.bin').write_bytes(stopped)
    state=status();pin=pin_status()
    assert state.get('done')=='0' and pin.get('guard_changes')=='0' and pin==pin_before
    result=dict(schema=1,nonce=nonce,mode=mode,stable=True,retained=True,
        admission=state,pin=pin,code=w[20],ticks=w[27],hardware_fault_tested=mode==3,nmi_hardware_tested=mode==4,
        nmi_owned=mode>=3,scsi_excluded=False)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def validate_runtime(page,nonce,seq,phase):
    w=validate(page,nonce,5,False)
    assert w[24]==0 and w[160]==0 and w[155]==0
    assert w[166]==seq and w[167]>=6 and w[168]>=2
    assert w[169:172]==(0,1,phase)
    return w

def runtime_sample(snap,write,nonce,seq,out,phase=0):
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
    validate_runtime(page,nonce,seq,phase)
    # No second sample request, so the card-owned report must stay immutable.
    assert snap(ADDRESS)[64:]==page[64:]
    return dict(sequence=seq,phase=phase,ticks=w[167],handoffs=w[168],owned=True)
