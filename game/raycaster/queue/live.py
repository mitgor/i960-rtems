#!/usr/bin/env python3
"""Fail-stop bounded queue test; every STEP retains a complete paired audit."""
import argparse,gzip,json,re,secrets,struct,sys,time
from pathlib import Path
from model import Model,Native,cases,validate,SIZE,OFFSET,ray_request
GAME=Path(__file__).resolve().parents[1];ROOT=GAME.parents[1]
sys.path.insert(0,str(ROOT/'rtems/transport'));from run import Board
sys.path.insert(0,str(GAME/'transfer'));from commands import parse
p=argparse.ArgumentParser();p.add_argument('--payload',type=Path,required=True);p.add_argument('--module',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--queue',action='store_true');p.add_argument('--pipeline',choices=['separate','combined']);a=p.parse_args()
if a.pipeline and not a.queue:p.error('--pipeline requires --queue')
if a.pipeline:
 from combined.model import Model,cases as pipeline_cases
 cases=lambda epoch:pipeline_cases(epoch=epoch,combined=a.pipeline=='combined')
epoch=secrets.randbelow(0xfffffffd)+1
model=Model() if a.queue else Native();rows=[]
b=Board(a.payload,a.module,a.output)
(a.output/'queue-test.json').write_text(json.dumps(dict(queue=a.queue,epoch=epoch,frames=80,pipeline=a.pipeline),indent=2)+'\n')
commands=gzip.open(a.output/'commands.jsonl.gz','wt');snapshots=gzip.open(a.output/'full-audits.bin.gz','wb')
try:
 requests=cases(epoch=epoch) if a.queue else [('init',ray_request(op=0,columns=0))]+[('render',ray_request(keys=i//10%16)) for i in range(80)]
 for label,data in requests:
  start=time.monotonic_ns();cpu=time.process_time_ns();reply=b.step(data);end=time.monotonic_ns();cpu_end=time.process_time_ns()
  seq=b.sequence
  assert reply==(model.step(data,seq) if a.queue else model.step(data)),(seq,label)
  first=(b.debugfs/'payload-after-a5.bin').read_bytes();second=(b.debugfs/'payload-after-5a.bin').read_bytes()
  assert len(first)==524288 and first==second
  # Every audit is retained, not merely the original every-32nd sample.
  snapshots.write(first);snapshots.flush()
  log=(b.debugfs/'result.txt').read_text();cmd=parse(log)
  audit=[x for x in cmd if x['op']==0x20 and x['offset']<524288 and x['count'] in (61440,32768)]
  assert [(x['offset'],x['count']) for x in audit]==[(off,min(61440,524288-off)) for _ in range(2) for off in range(0,524288,61440)]
  targeted={}
  if a.queue:
   assert first[OFFSET:OFFSET+2*SIZE]==b''.join(model.slots)
   assert (b.debugfs/'frame-descriptor-a5.bin').read_bytes()==reply==(b.debugfs/'frame-descriptor-5a.bin').read_bytes()
   for slot in range(2):
    if not model.mask&(1<<slot):continue
    one=(b.debugfs/f'frame-slot{slot}-a5.bin').read_bytes();two=(b.debugfs/f'frame-slot{slot}-5a.bin').read_bytes()
    assert one==two==model.slots[slot];validate(one,model.epoch,model.gen[slot],slot);targeted[str(slot)]=one.hex()
  match=re.search(r'RAYPROFILE seq=(\d+) upload=(\d+) arm=(\d+) execute=(\d+) verify=(\d+) audit=(\d+) total=(\d+) bytes=(\d+)',log);assert match
  row=dict(zip(['sequence','upload_ns','arm_ns','execute_ns','verify_ns','audit_ns','kernel_ns','audit_bytes'],map(int,match.groups())))
  row.update(label=label,wall_ns=end-start,cpu_ns=cpu_end-cpu)
  if a.queue:
   q=re.search(r'FQPROFILE seq=(\d+) mask=(\d+) targeted_ns=(\d+) full_audit_ns=(\d+)',log);assert q
   qs,mask,target,full=map(int,q.groups());assert qs==seq and mask==model.mask
   row.update(mask=mask,targeted_ns=target,full_audit_ns=full)
  rows.append(row);commands.write(json.dumps(dict(sequence=seq,commands=cmd,log=log,slots=targeted))+'\n');commands.flush()
  (a.output/'phases.json').write_text(json.dumps(rows,indent=2)+'\n')
finally:
 try:print(json.dumps(b.close()))
 finally:commands.close();snapshots.close()
print('PASS',len(rows),'full audits and replies',flush=True)
