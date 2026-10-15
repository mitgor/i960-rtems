#!/usr/bin/env python3
import copy,json,struct,tempfile
from pathlib import Path
from verify_release import verify
with tempfile.TemporaryDirectory() as d:
 d=Path(d)
 base={'test-options.json':dict(release_schedule='priority'),'doom-pingpong-result.json':dict(frames=18),
 'audit-gate.jsonl':[dict(page=0,begin=i,words=4,start_ns=i+1,acquired_ns=i+2,end_ns=i+3) for i in range(0,64,4)],
 'control-journal.jsonl':[dict(op=5) for i in range(64)],
 'pingpong-journal.jsonl':[dict(request=struct.pack('<8I',4,42,17,0,0,0,0,0).hex(),start_ns=100,acquired_ns=150,end_ns=170,gate_wait_ns=50,ioctl_ns=20,ns=70,release_priority=True)],
 'browser-publish.jsonl':[dict(frame=g,priority=True,observed=0.00000001,published=0.00000005) for g in (17,18)]}
 def save(v):
  for name,x in v.items():(d/name).write_text(''.join(json.dumps(z)+'\n' for z in x) if name.endswith('.jsonl') else json.dumps(x))
 save(base);assert verify(d)['full_frozen_pages']==1
 single=copy.deepcopy(base);single['audit-gate.jsonl']=[dict(page=0,begin=i,words=1,start_ns=i+1,acquired_ns=i+2,end_ns=i+3) for i in range(64)];save(single);assert verify(d)['audit_groups']==64
 for field,value in [('gate_wait_ns',49),('ioctl_ns',21),('ns',71),('release_priority',False),('acquired_ns',99)]:
  v=copy.deepcopy(base);v['pingpong-journal.jsonl'][0][field]=value;save(v)
  try:verify(d)
  except AssertionError:pass
  else:raise AssertionError(field)
 for field,value in [('begin',1),('words',3),('page',1)]:
  v=copy.deepcopy(base);v['audit-gate.jsonl'][1][field]=value;save(v)
  try:verify(d)
  except AssertionError:pass
  else:raise AssertionError(field)
print('PASS split timing identity, priority policy, complete frozen-page coverage; eight mutations rejected')
