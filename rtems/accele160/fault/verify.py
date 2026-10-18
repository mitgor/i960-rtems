#!/usr/bin/env python3
"""Replay a terminal/ directory. Physical evidence requires actual captures."""
import argparse,json
from pathlib import Path
from host import validate

def verify(path):
    r=json.loads((path/'result.json').read_text());nonce=r['nonce'];mode=r['mode']
    before=(path/'ready.bin').read_bytes();validate(before,nonce,mode,False)
    assert (path/'stale.bin').read_bytes()[64:]==before[64:]
    terminal=(path/'terminal.bin').read_bytes();validate(terminal,nonce,mode,True)
    assert terminal==(path/'stable.bin').read_bytes()==(path/'after-stop.bin').read_bytes()
    assert r['retained'] and r['admission']['done']=='0' and r['pin']['guard_changes']=='0'
    if mode==4:
        armed=(path/'armed.bin').read_bytes();aw=validate(armed,nonce,mode,False)
        assert aw[155]==1 and r['nmi_hardware_tested']
    assert r['hardware_fault_tested']==(mode==3) and r['nmi_owned']==(mode>=3) and not r['scsi_excluded']
    return dict(mode=mode,code=hex(r['code']),stable=True,retained=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args()
    print(json.dumps(verify(a.capture),indent=2))
