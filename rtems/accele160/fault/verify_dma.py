#!/usr/bin/env python3
"""Replay an active-DMA terminal archive; never execute archived code."""
import argparse,hashlib,json,struct,tarfile
from host import validate,dma_fnv,dma_descriptors,validate_dma_observation,validate_dma_frame
sha=lambda b:hashlib.sha256(b).hexdigest()
def verify(path):
    with tarfile.open(path) as t:
        files={m.name:t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
    def read(n):return files[n]
    def obj(n):return json.loads(read(n))
    for n,h in obj('bundle/bundle.json')['files'].items():assert sha(read('bundle/'+n))==h,n
    result,=[n for n in files if n.endswith('/run/terminal/result.json')]
    terminal=result[:-11];session=terminal[:-13];r=obj(result);mode=r['mode'];nonce=r['nonce']
    assert mode in (6,7,8,9,10,11,12,13)
    assert r['hardware_fault_tested']==(mode in (6,8,10,12)) and r['nmi_hardware_tested']==(mode in (7,9,11,13))
    ready=read(terminal+'ready.bin');validate(ready,nonce,mode,False)
    assert read(terminal+'stale.bin')[64:]==ready[64:]
    raw=read(terminal+'terminal.bin');w=validate(raw,nonce,mode,True)
    assert raw==read(terminal+'stable.bin')==read(terminal+'after-stop.bin')
    validate_dma_observation(w)
    if mode in (11,13):
        assert obj(terminal+'mu-after.json')==dict(idr=w[222],iisr=w[221],iimr=w[223])
    if mode in (7,9,11,13):assert validate(read(terminal+'armed.bin'),nonce,mode,False)[155]==1
    expected=bytes((i^(i>>8)^0x69)&255 for i in range(65536))
    assert w[192]==dma_fnv(expected) and w[194]==1
    for off in range(0,65536,8192):
        assert read(terminal+f'source-{off:05x}.bin')==expected[off:off+4096]
    for slot in (0,1):
        b=read(terminal+f'frame{slot}.bin');validate_dma_frame(b,slot,mode in (8,9,12,13))
        if mode>=8:assert b==read(terminal+f'delayed-frame{slot}.bin')
    descriptors=dma_descriptors(w);assert w[193]==dma_fnv(descriptors)
    for off in range(0,32800,8192):
        n=min(4096,32800-off)
        assert read(terminal+f'descriptors-{off:05x}.bin')[:n]==descriptors[off:off+n]
    assert read(terminal+'owner-after.bin')[0x2a0:0xaa0]==read(session+'run/owner-reserved.bin')[0x2a0:0xaa0]
    assert obj(terminal+'release-denied.json')['returncode']!=0
    assert r['admission']['done']=='0' and r['admission']['released']=='0'
    assert r['pin']['retained']=='1' and r['pin']['guard_changes']=='0'
    assert int(r['pin']['bus0'],16)==w[182]
    assert all(r[k] for k in ('retained','active_dma_at_entry',
        'dma_source_retained','dma_destination_retained','completion_not_synthesized'))
    assert r['drained_after_terminal']==(mode<8 or mode in (10,11))
    if mode>=8:assert r['stalled_timeout']
    if mode in (10,11):assert r['resumed_after_timeout']
    if mode in (12,13):assert r['resume_refused'] and not r['resumed_after_timeout']
    if mode>=8:
        exit_state=obj(session+'run/post-owner-exit.json')
        assert exit_state['boot_id']==obj(session+'run/result.json')['boot_id']
        assert exit_state['owner_unit'] in ('inactive','failed','unknown')
        assert exit_state['admission']['done']=='0' and exit_state['admission']['released']=='0'
        assert exit_state['pin']==r['pin']
        for slot in (0,1):assert exit_state['frame_sha256'][str(slot)]==sha(read(terminal+f'frame{slot}.bin'))
    symbols={a[2]:int(a[0],16) for line in read('bundle/kernel/kernel.symbols').decode().splitlines() if len(a:=line.split())==3}
    assert w[148]==symbols['_accele_fault_entry'] and w[149]==symbols['_accele_nmi_entry']
    if mode in (6,8,10,12):assert w[164]==symbols['_accele_raise_fault']+4
    m=obj('bundle/project/rtems/accele160/doom_dma/persistent-manifest.json');assert m['terminal_test']==mode
    for n in ('kernel','image'):assert sha(read('bundle/kernel/'+n+'.bin'))==m[n+'_sha256']
    for n,h in m['terminal_sources'].items():assert sha(read('bundle/project/rtems/accele160/fault/'+n))==h
    assert sha(read('bundle/project/rtems/accele160/doom_dma/frame_dma.h'))==m['dma_source_sha256']
    boots=[]
    for i in (0,1):
        prefix=session+f'pre-{i}/'
        assert sha(read(prefix+'data.bin'))=='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
        s=dict(x.split('=') for x in read(prefix+'status.txt').decode().split())
        assert s['done']=='1' and all(s[k]=='0' for k in ('status','residual','guard_changes'))
        boots.append(obj(prefix+'request.json')['boot_id'])
    assert boots[0]==boots[1]==obj(session+'run/result.json')['boot_id']
    return dict(mode=mode,boot_id=boots[0],kernel_sha256=m['kernel_sha256'],paired_firmware=True,
        entry_csr=hex(w[176]),entry_ccr=hex(w[177]),post_owner_exit_verified=mode>=8,entry_next_descriptor=hex(w[178]),entry_byte_count=w[179],
        resume_refused=mode in (12,13),refusal_observer_polls=w[228] if mode in (12,13) else None,resumed_after_timeout=mode in (10,11),resume_polls=w[210] if mode in (10,11) else None,stalled_timeout=mode>=8,terminal_seconds=r.get('terminal_seconds'),drain_polls=w[175],drain_csr=hex(w[186]),finite_bytes=1024*65536,
        fault_or_nmi_record=[hex(v) for v in w[161:165]],source_chain_fnv_and_visible_page_checks=True,
        guards_intact=True,second_target_untouched=True,release_denied=True,retained=True,
        post_test_reset_verified=False)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive');a=p.parse_args()
    print(json.dumps(verify(a.archive),indent=2))
