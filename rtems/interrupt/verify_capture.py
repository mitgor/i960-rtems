#!/usr/bin/env python3
"""Revalidate archived owned-stack binaries, raw register records and cleanup."""
import argparse,hashlib,json,struct,subprocess,sys,tarfile,tempfile
from pathlib import Path
from live_context import decode
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'control'))
from run import verify_close
from protocol import response
import wire
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);a=p.parse_args()
with tarfile.open(a.archive) as archive,tempfile.TemporaryDirectory(prefix='irq-context-verify-') as tmp:
    def read(name):return archive.extractfile(name).read()
    for profile,module,run in [('irqctx','irqctx-bounded/dac960rtems.ko','irqctx-live1'),('muctx','muctx-module/dac960auto.ko','muctx-live1')]:
        identity=json.loads(read(run+'/request.json'));payload=read(profile+'/kernel.bin')
        for key,data in [('payload_sha256',payload),('image_sha256',wire.prepare(payload)),('module_sha256',read(module))]:
            assert identity[key]==hashlib.sha256(data).hexdigest(),key
        build=Path(tmp)/profile;build.mkdir()
        for name in ['kernel.symbols','kernel.dis']:(build/name).write_bytes(read(profile+'/'+name))
        subprocess.run([sys.executable,str(Path(__file__).with_name('check_build.py')),str(build)],check=True)
        close=build/'close';close.mkdir()
        for member in archive.getmembers():
            prefix=run+'/close/'
            if member.isfile() and member.name.startswith(prefix):
                name=member.name[len(prefix):];assert name and '/' not in name and name not in ('.','..')
                (close/name).write_bytes(read(member.name))
        verify_close(close)
        summary=json.loads(read(run+'/summary.json'));assert summary['restored'] and summary['unloaded'] and not summary['driver_bound']
    rows=json.loads(read('irqctx-live1/acceptance.json'))
    assert len(rows)==3
    for i,row in enumerate(rows):assert decode(read(f'irqctx-live1/context-{i}.bin'))==row
    epoch=json.loads(read('muctx-live1/control-acceptance.json'))['epoch']
    replies={}
    for record in json.loads(read('muctx-live1/exchanges.json')):
        raw=read('muctx-live1/'+record['label']+'.bin');w=struct.unpack('<36I',raw)
        assert w[34:]==(1,1)
        if record['label']=='halt':assert w[16]==0x2f000000;continue
        reply=response(raw[64:128],epoch,w[0]);assert reply==record['response'];replies[record['label']]=reply
    assert replies['stop']==replies['stop-retry']==replies['stopped-status'] and replies['stop']['stopped']
    assert replies['ping']==replies['ping-retry'] and replies['ping']['value']==0x960cafe
    assert replies['wrong-epoch']['status']==2 and replies['bad-checksum']['status']==1
    w=struct.unpack('<98I',read('muctx-live1/irq-stack.bin'))
    assert w[17]>100 and w[18]==w[19]==w[28]==0
    assert w[26]+192<=w[20]<=w[21]<w[26]+w[27]-64
    assert w[29]==0xc0001000 and w[15]==0
    before=json.loads(read('muctx-live1/mu-before.json'))['samples'][0]
    for row in json.loads(read('muctx-live1/mu-after.json'))['samples']:
        for key in ['IMR1','OMR1','IIMR','OIMR']:assert row[key]==before[key]
        for key in ['IISR','OISR']:assert int(row[key],16)&2==int(before[key],16)&2
print('Verified both linked builds and binaries; 126 stress interrupts, framed STOP/HALT, raw context/guard results and full borrowed-RAM cleanup')
