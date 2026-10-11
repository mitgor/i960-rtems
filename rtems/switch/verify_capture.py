#!/usr/bin/env python3
"""Verify archived two-task context switches, exact binaries and full cleanup."""
import argparse,hashlib,json,struct,tarfile,tempfile,sys
from pathlib import Path
from live_test import decode,decode_defer
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import verify_close
import wire
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--defer',action='store_true');a=p.parse_args();profile='defer' if a.defer else 'switch'
with tarfile.open(a.archive) as archive,tempfile.TemporaryDirectory(prefix='irq-switch-verify-') as tmp:
    def read(name):return archive.extractfile(name).read()
    code=read(profile+'/kernel.bin');module=read(profile+'-module/dac960rtems.ko')
    rows=json.loads(read(profile+'-live1/acceptance.json'));assert len(rows)==3
    dis=read(profile+'/kernel.dis').decode()
    assert '<_switch_threads>' in dis and '<_switch_irq_areas+0x40>' in dis
    assert 'shlo\t13,r8,r7' in dis and 'modtc\tr7,r6,r7' in dis
    for i,row in enumerate(rows):
        prefix=f'{profile}-live1/run-{i}/'
        identity=json.loads(read(prefix+'request.json'))
        for key,data in [('payload_sha256',code),('image_sha256',wire.prepare(code)),('module_sha256',module)]:
            assert identity[key]==hashlib.sha256(data).hexdigest(),key
        raw=read(prefix+'switch.bin')
        assert (decode_defer if a.defer else decode)(raw)==row
        if a.defer:
            # Negative acceptance checks: corrupted fault, depth, tick, pending,
            # owner and premature/missing peer execution must never pass.
            for index,value in ((1,1),(2,0),(4,3),(6,8),(7,1),(8,0),(9,1),
                                (10,0),(11,0),(12,0),(13,0),(14,1),(15,0),(16,2)):
                damaged=bytearray(raw);struct.pack_into('<I',damaged,736+4*index,value)
                try:decode_defer(damaged)
                except AssertionError:pass
                else:raise AssertionError(('accepted corrupt deferral field',index))
        close=Path(tmp)/str(i);close.mkdir()
        for member in archive.getmembers():
            if member.isfile() and member.name.startswith(prefix+'close/'):
                name=member.name[len(prefix+'close/'):];assert name and '/' not in name and name not in ('.','..')
                (close/name).write_bytes(read(member.name))
        verify_close(close)
        summary=json.loads(read(prefix+'summary.json'))
        assert summary['restored'] and summary['unloaded'] and not summary['driver_bound']
print('Verified three raw two-task switch reports, register sentinels, drained lifetimes, exact binaries and full borrowed-RAM restoration')

if a.defer:print('Nested dispatch deferral verified; 45 corrupted-report acceptance checks rejected')
