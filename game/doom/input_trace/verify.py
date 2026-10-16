#!/usr/bin/env python3
"""Reconcile full input trace with successful host submissions; no timing waiver."""
import argparse,json,struct,sys
from pathlib import Path
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'rtems/residentnet'))
from presentation_profile import decode
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args();c=a.capture
options=json.loads((c/'presentation-options.json').read_text());assert options['input_trace']
frames=[json.loads(x) for x in (c/'play-frames.jsonl').read_text().splitlines()]
assert len(frames)==520 and all(f['session']==0 for f in frames)
events=[];total=0
for f in frames:
 raw=(c/f"play-0-{f['frame']}.bin").read_bytes();trace=decode(raw,f['frame'],options=options)['input_trace']
 assert trace==f['profile']['input_trace']
 assert trace['total']==total+len(trace['events']);total=trace['total'];events.extend(trace['events'])
submissions=[json.loads(s) for s in (c/'input-submit.jsonl').read_text().splitlines()]
success=[r for r in submissions if r['result']==0]
phases={phase:[r for r in events if r[1]==phase] for phase in (1,2,3)}
for phase,rows in phases.items():assert [r[5] for r in rows]==[r['key'] for r in success],(phase,'input mismatch')
assert len(success)==8,'bounded script must submit four key-down/up pairs'
result=[]
for i,submit in enumerate(success):
 dequeue,before,after=[phases[p][i] for p in (1,2,3)]
 assert dequeue[0]<before[0]<after[0] and before[2:6]==after[2:6]
 assert dequeue[2]<=before[2] and submit['observed_frame']<dequeue[2]
 result.append(dict(submitted_after_frame=submit['observed_frame'],key=submit['key'],dequeue_frame=dequeue[2],responder_frame=before[2],gametic=before[3],maketic=before[4],menu_before=before[6],menu_after=after[6]))
# Actual captures must reject format corruption, overflow and sequence tampering.
raw=(c/'play-0-1.bin').read_bytes();rejected=0
for offset,value in [(65024,0),(65028,2),(65032,9),(65036,17),(65044,1),(65532,1)]:
 bad=bytearray(raw);struct.pack_into('<I',bad,offset,value)
 try:decode(bad,1,options=options)
 except AssertionError:rejected+=1
 else:raise AssertionError((offset,value))
print(json.dumps(dict(frames=len(frames),events=total,submissions=len(submissions),accepted=len(success),mutation_refusals=rejected,input=result),indent=2))
