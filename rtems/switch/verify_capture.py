#!/usr/bin/env python3
"""Verify archived two-task context switches, exact binaries and full cleanup."""
import argparse,hashlib,json,struct,tarfile,tempfile,sys
from pathlib import Path
from live_test import decode
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import verify_close
import wire
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);a=p.parse_args()
with tarfile.open(a.archive) as archive,tempfile.TemporaryDirectory(prefix='irq-switch-verify-') as tmp:
    def read(name):return archive.extractfile(name).read()
    code=read('switch/kernel.bin');module=read('switch-module/dac960rtems.ko')
    rows=json.loads(read('switch-live1/acceptance.json'));assert len(rows)==3
    dis=read('switch/kernel.dis').decode()
    assert '<_switch_threads>' in dis and '<_switch_irq_areas+0x40>' in dis
    assert 'shlo\t13,r8,r7' in dis and 'modtc\tr7,r6,r7' in dis
    for i,row in enumerate(rows):
        prefix=f'switch-live1/run-{i}/'
        identity=json.loads(read(prefix+'request.json'))
        for key,data in [('payload_sha256',code),('image_sha256',wire.prepare(code)),('module_sha256',module)]:
            assert identity[key]==hashlib.sha256(data).hexdigest(),key
        assert decode(read(prefix+'switch.bin'))==row
        close=Path(tmp)/str(i);close.mkdir()
        for member in archive.getmembers():
            if member.isfile() and member.name.startswith(prefix+'close/'):
                name=member.name[len(prefix+'close/'):];assert name and '/' not in name and name not in ('.','..')
                (close/name).write_bytes(read(member.name))
        verify_close(close)
        summary=json.loads(read(prefix+'summary.json'))
        assert summary['restored'] and summary['unloaded'] and not summary['driver_bound']
print('Verified three raw two-task switch reports, register sentinels, drained lifetimes, exact binaries and full borrowed-RAM restoration')
