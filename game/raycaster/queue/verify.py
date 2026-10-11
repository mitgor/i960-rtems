#!/usr/bin/env python3
"""Replay every full audit, queue transition and targeted read against the oracle."""
import argparse,gzip,hashlib,json,re,struct,sys
from pathlib import Path
from model import Model,Native,cases,ray_request,validate,SIZE,OFFSET
GAME=Path(__file__).resolve().parents[1];ROOT=GAME.parents[1]
sys.path.insert(0,str(ROOT/'rtems/transport'));from run import verify_close,ROM_SHA
import wire
sys.path.insert(0,str(GAME/'transfer'));from commands import parse
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--payload',type=Path,required=True);p.add_argument('--module',type=Path,required=True);a=p.parse_args();cap=a.capture
meta=json.loads((cap/'request.json').read_text());cfg=json.loads((cap/'queue-test.json').read_text());queue=cfg['queue']
if cfg.get('pipeline'):
 assert queue and cfg['pipeline'] in ('separate','combined')
 from combined.model import Model,cases as pipeline_cases
 cases=lambda epoch:pipeline_cases(epoch=epoch,combined=cfg['pipeline']=='combined')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(a.payload)==meta['payload_sha256'] and sha(a.module)==meta['module_sha256']
image=wire.prepare(a.payload.read_bytes());assert hashlib.sha256(image).hexdigest()==meta['image_sha256']
original=(cap/'open/stage-before-a5.bin').read_bytes();assert hashlib.sha256(original).hexdigest()==ROM_SHA
assert original==(cap/'open/stage-before-5a.bin').read_bytes()
verify_close(cap/'close');summary=json.loads((cap/'summary.json').read_text());assert summary['restored'] and summary['unloaded'] and not summary['driver_bound']
raw=gzip.decompress((cap/'trace.bin.gz').read_bytes());phases=json.loads((cap/'phases.json').read_text())
requests=list(cases(epoch=cfg['epoch'])) if queue else [('init',ray_request(op=0,columns=0))]+[('render',ray_request(keys=i//10%16)) for i in range(80)]
assert len(requests)==len(phases)==summary['steps']
model=Model() if queue else Native();pos=0;frames=commands=0
with gzip.open(cap/'commands.jsonl.gz','rt') as logs,gzip.open(cap/'full-audits.bin.gz','rb') as audits:
 for seq,((label,req),phase,line) in enumerate(zip(requests,phases,logs),1):
  elapsed,n=struct.unpack_from('<QI',raw,pos);pos+=12;incoming=raw[pos:pos+n];pos+=n
  n,=struct.unpack_from('<I',raw,pos);pos+=4;out=raw[pos:pos+n];pos+=n
  assert incoming==req and phase['sequence']==seq and phase['label']==label
  assert out==(model.step(req,seq) if queue else model.step(req))
  after=audits.read(524288);assert len(after)==phase['audit_bytes']==524288
  before=image[:wire.bio.OFFSET]+wire.block(req,seq)+original[wire.bio.IMAGE_SIZE:]
  assert wire.response(before,after)==(0,out)
  sample=json.loads(line);assert sample['sequence']==seq and parse(sample['log'])==sample['commands']
  rows=sample['commands'];commands+=len(rows)
  table=(0xc001f9bc-0xc0f2c000)&0xffffffff;quiet=(0xc004cec0-0xc0f2c000)&0xffffffff
  expected=([(0x20,80,quiet)]*2 if seq>1 else [])+[(0x21,0x3060,0x70000)]
  if seq==1:
   expected += [(0x21,4,table),(0x20,4,table),(0x20,4,table),(0x6f,0,0)]
   for address,size in [(0xc011e22c,4),(0xc0110860,8),(0xc000a2a0,256),(0xc000a120,104),(0xc004cec0,80)]:expected += [(0x20,size,(address-0xc0f2c000)&0xffffffff)]*2
   expected += [(0x21,4,quiet),(0x6f,0,0)]+[(0x20,80,quiet)]*2
  expected += [(0x21,16,0x80280),(0x21,4,table),(0x20,4,table),(0x20,4,table),(0x6f,0,0),(0x20,4,table),(0x20,4,table),(0x20,16,0x80280),(0x20,16,0x80280)]
  if queue:
   q=re.search(r'FQPROFILE seq=(\d+) mask=(\d+) targeted_ns=(\d+) full_audit_ns=(\d+)',sample['log']);assert q
   assert list(map(int,q.groups()))==[seq,model.mask,phase['targeted_ns'],phase['full_audit_ns']]
   assert phase['targeted_ns']+phase['full_audit_ns']<=phase['audit_ns']
   expected += [(0x20,64,0x70000+wire.bio.OUTPUT)]*2
   assert after[OFFSET:OFFSET+2*SIZE]==b''.join(model.slots)
   assert set(sample['slots'])=={str(i) for i in range(2) if model.mask&(1<<i)}
   for i in range(2):
    if model.mask&(1<<i):
     expected += [(0x20,SIZE,OFFSET+i*SIZE)]*2
     data=bytes.fromhex(sample['slots'][str(i)]);assert data==model.slots[i];validate(data,model.epoch,model.gen[i],i);frames+=1
  expected += [(0x20,min(61440,524288-off),off) for _ in range(2) for off in range(0,524288,61440)]
  assert [(r['op'],r['count'],r['offset']) for r in rows]==expected,(seq,label)
  assert sum(phase[k] for k in ['upload_ns','arm_ns','execute_ns','verify_ns','audit_ns'])==phase['kernel_ns']
 assert seq==len(requests) and not audits.read(1) and not logs.read() and pos==len(raw)
print(json.dumps(dict(replies=len(requests),full_audits=len(requests),targeted_slots=frames,commands=commands,restored=True,unloaded=True,boot_id=meta['boot_id']),indent=2))
