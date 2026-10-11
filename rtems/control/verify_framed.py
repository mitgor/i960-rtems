#!/usr/bin/env python3
"""Verify archived framed MU acceptance and the full borrowed-RAM restoration."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import tarfile
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
import wire
from run import verify_close
from protocol import response
p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path);a=p.parse_args()
with tarfile.open(a.archive) as archive:
    def read(name):return archive.extractfile(name).read()
    def run(name):return read('muctl-live1/'+name)
    identity=json.loads(run('request.json'))
    payload=read('muctl/kernel.bin');module=read('muctl-module/dac960auto.ko')
    for key,data in [('payload_sha256',payload),('image_sha256',wire.prepare(payload)),('module_sha256',module)]:
        assert identity[key]==hashlib.sha256(data).hexdigest(),key
    accepted=json.loads(run('control-acceptance.json'));epoch=accepted['epoch']
    records=json.loads(run('exchanges.json'));assert len(records)==9
    parsed={}
    for row in records:
        data=run(row['label']+'.bin');w=struct.unpack('<36I',data)
        assert w[34:]==(1,1) and row['firmware_sequence']==[1,1]
        assert w[32]==row['generation']
        r={'halt_ack':hex(w[16])} if row['label']=='halt' else response(data[64:128],epoch,w[0])
        assert row['response']==r;parsed[row['label']]=r
    assert parsed['ping']==parsed['ping-retry']
    assert parsed['ping']['status']==0 and parsed['ping']['value']==0x960cafe
    assert parsed['wrong-epoch']['status']==2 and parsed['bad-checksum']['status']==1
    assert parsed['stop']==parsed['stop-retry']==parsed['stopped-status']
    assert parsed['stop']['stopped'] and parsed['stop']['status']==0
    assert parsed['stop']['value']>parsed['status']['value']
    assert parsed['halt']['halt_ack']=='0x2f000000'
    before=json.loads(run('mu-before.json'))['samples'][0]
    for row in json.loads(run('mu-after.json'))['samples']:
        for n in ['IMR1','OMR1','IIMR','OIMR']:assert row[n]==before[n],n
        for n in ['IISR','OISR']:assert int(row[n],16)&2==int(before[n],16)&2,n
    with tempfile.TemporaryDirectory(prefix='i960-framed-verify-') as tmp:
        for member in archive.getmembers():
            prefix='muctl-live1/close/'
            if member.isfile() and member.name.startswith(prefix):
                name=member.name[len(prefix):]
                assert name and '/' not in name and name not in ('.','..')
                (Path(tmp)/name).write_bytes(read(member.name))
        verify_close(Path(tmp))
        log=(Path(tmp)/'result.txt').read_text()
        assert 'AUTONOMOUS STOP verified before any RAM restoration' in log
        assert 'MU message words/masks/pending restored by target plus host OISR ack' in log
    restored=json.loads(run('restoration.json'))
    assert restored['restored'] and restored['unloaded'] and not restored['driver_bound']
print('Verified pinned binaries, raw CTL1 replies/sequences, independent bounded STOP/HALT, full RAM/MU restoration and unload record')
