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
    return struct.unpack_from('<160I',page)

def validate(page,nonce,mode,terminal):
    w=decode(page)
    assert w[16:19]==(MAGIC,nonce,1) and w[25]==mode
    assert w[31]==(DONE if terminal else READY)
    assert w[32]==0xfeffdd20 and w[64]==0xc0000800
    assert w[26]==(0 if terminal and mode==2 else 1)
    if terminal:
        assert w[20]==0x7d000+mode and w[24]==1 and w[28]==1
        assert w[38]==0 and w[44]==125000 and w[45]<=125000
        assert w[48:57]==(0,)*9 # injections are before DMA initialization
    return w

def exercise(snap,write,nonce,mode,out,status,pin_status):
    assert mode in (1,2)
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
    write(ADDRESS,0,struct.pack('<3I',nonce,1,0x54455354))
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
        admission=state,pin=pin,code=w[20],ticks=w[27],hardware_fault_tested=False,
        nmi_owned=False,scsi_excluded=False)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
