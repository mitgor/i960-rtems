#!/usr/bin/env python3
"""Replay one immutable owned-exception bundle/session archive, without extraction."""
import argparse,hashlib,json,struct,tarfile
from host import validate
FIRMWARE='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
def verify(path):
    with tarfile.open(path) as t:
        def read(n):return t.extractfile(n).read()
        def obj(n):return json.loads(read(n))
        results=[n.name for n in t.getmembers() if n.name.endswith('/run/terminal/result.json')]
        assert len(results)==1
        terminal=results[0][:-11];session=terminal[:-13]
        r=obj(results[0]);mode=r['mode'];nonce=r['nonce'];assert mode in (3,4)
        before=read(terminal+'ready.bin');validate(before,nonce,mode,False)
        assert read(terminal+'stale.bin')[64:]==before[64:]
        raw=read(terminal+'terminal.bin');w=validate(raw,nonce,mode,True)
        assert raw==read(terminal+'stable.bin')==read(terminal+'after-stop.bin')
        assert r['retained'] and r['admission']['done']=='0' and r['pin']['guard_changes']=='0'
        assert r['hardware_fault_tested']==(mode==3) and r['nmi_hardware_tested']==(mode==4)
        assert r['nmi_owned'] and not r['scsi_excluded']
        if mode==4:
            armed=validate(read(terminal+'armed.bin'),nonce,mode,False);assert armed[155]==1
        symbols={a[2]:int(a[0],16) for line in read('bundle/kernel/kernel.symbols').decode().splitlines() if len(a:=line.split())==3}
        assert w[148]==symbols['_accele_fault_entry'] and w[149]==symbols['_accele_nmi_entry']
        if mode==3:assert w[164]==symbols['_accele_raise_fault']+4
        manifest=obj('bundle/project/rtems/accele160/doom_dma/persistent-manifest.json')
        for name in ('kernel','image'):
            assert hashlib.sha256(read('bundle/kernel/'+name+'.bin')).hexdigest()==manifest[name+'_sha256']
        assert manifest['terminal_test']==mode
        for name,h in manifest['terminal_sources'].items():
            assert hashlib.sha256(read('bundle/project/rtems/accele160/fault/'+name)).hexdigest()==h
        first=read(session+'pre-0/data.bin');second=read(session+'pre-1/data.bin')
        assert len(first)==1048576 and first==second and hashlib.sha256(first).hexdigest()==FIRMWARE
        for n in ('pre-0','pre-1'):
            status=read(session+n+'/status.txt').decode()
            assert 'done=1' in status and 'status=0' in status and 'residual=0' in status and 'guard_changes=0' in status
        top=obj(session+'run/result.json')
        return dict(mode=mode,boot_id=top['boot_id'],kernel_sha256=manifest['kernel_sha256'],
            paired_firmware=True,ticks=w[27],fault_entry=hex(w[148]),nmi_entry=hex(w[149]),
            raw_record=[hex(v) for v in w[161:165]],
            nmi_sources=[hex(v) for v in w[151:155]] if mode==4 else None,guards_intact=True,stable=True,retained=True,
            hardware_fault_tested=mode==3,nmi_hardware_tested=mode==4,post_test_reset_verified=False)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive');a=p.parse_args()
    print(json.dumps(verify(a.archive),indent=2))
