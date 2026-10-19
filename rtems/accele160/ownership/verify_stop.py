#!/usr/bin/env python3
"""Check final STOP and report continuity against the separately verified live run."""
import hashlib,json,struct,sys,tarfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'fault'))
from host import validate_runtime
from inventory import decode

def read(path):
    with tarfile.open(path) as t:return {m.name:t.extractfile(m).read() for m in t if m.isfile()}
def verify(live,final):
    before=read(live);files=read(final)
    name,=[n for n in files if n.endswith('/run/owned-quiescent.bin')]
    run=name[:-len('owned-quiescent.bin')]
    samples=json.loads(files[run+'owned-runtime.json']);assert len(samples)==4
    for row in samples[:-1]:
        n=run+'owned-'+row['label']+'.bin';assert files[n]==before[n]
    row=samples[-1];assert row['label']=='quiescent' and row['phase']==1
    page=files[name];nonce=struct.unpack_from('<I',page,68)[0]
    assert nonce==struct.unpack_from('<I',before[run+'owned-ready.bin'],68)[0]
    assert row['sequence']==samples[-2]['sequence']
    mode=json.loads(before['bundle/project/rtems/accele160/doom_dma/persistent-manifest.json'])['terminal_test']
    assert mode in (14,15)
    w=validate_runtime(page,nonce,row['sequence'],1,mode)
    inv=decode(page,nonce,row['sequence'],1)
    if mode==15:
        from qlogic_config import decode as config_decode
        inv['qlogic']=config_decode(page,nonce,row['sequence'],1)
    assert w[167]>=samples[-2]['ticks'] and w[168]>=samples[-2]['handoffs']
    q=files[run+'persist/quiescent-page.bin']
    assert struct.unpack_from('<2I',q,0xb54)==(0x45495551,0)
    assert struct.unpack_from('<I',q,0xa54)[0]==0x214b4341
    st=dict(x.split('=') for x in files[run+'persist/admit-pending-status.txt'].decode().split())
    pin=dict(x.split('=') for x in files[run+'persist/dma-pin-final.txt'].decode().split())
    assert st['done']=='0' and st['released']=='0' and pin['retained']=='1' and pin['guard_changes']=='0'
    return dict(quiescent=True,stop_ack=True,pending_callback=True,pins_retained=True,owned_guards=True,
        live_archive_sha256=hashlib.sha256(Path(live).read_bytes()).hexdigest(),final_engine_sample=inv)
if __name__=='__main__':print(json.dumps(verify(*sys.argv[1:]),indent=2))
