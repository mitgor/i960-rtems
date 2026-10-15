"""Replay split lock/ioctl timing and audit grouping; preserve old captures."""
import json,struct
from io_gate import release_policy

def verify(out):
 options=json.loads((out/'test-options.json').read_text())
 if 'release_schedule' not in options:return None
 schedule=options['release_schedule'];rows=lambda n:[json.loads(s) for s in (out/n).read_text().splitlines()]
 groups=rows('audit-gate.jsonl');assert groups
 expected=0;page=None;pages=0
 for x in groups:
  assert x['words'] in (1,4) and x['start_ns']<=x['acquired_ns']<x['end_ns']
  if not expected:page=x['page']
  assert x['page']==page and x['begin']==expected
  expected+=x['words'];assert expected<=64
  if expected==64:expected=0;pages+=1
 assert not expected
 controls=rows('control-journal.jsonl');assert sum(x.get('op')==5 for x in controls)==sum(x['words'] for x in groups)
 releases={}
 for x in rows('pingpong-journal.jsonl'):
  assert x['start_ns']<=x['acquired_ns']<x['end_ns']
  assert x['gate_wait_ns']==x['acquired_ns']-x['start_ns'] and x['ioctl_ns']==x['end_ns']-x['acquired_ns'] and x['ns']==x['gate_wait_ns']+x['ioctl_ns']
  if 'request' in x:op,e,g,off=struct.unpack_from('<4I',bytes.fromhex(x['request']))
  else:op,g=x['op'],x['g']
  assert x['release_priority']==(op==4 and release_policy(schedule,g))
  if op==4 and 'errno' not in x:releases[g]=x
 frames=json.loads((out/'doom-pingpong-result.json').read_text())['frames'];pub=rows('browser-publish.jsonl')
 assert [x['frame'] for x in pub]==list(range(17,frames+1))
 for x in pub:
  assert x['priority']==release_policy(schedule,x['frame']) and x['published']>=x['observed']
  if x['frame'] in releases:
   r=releases[x['frame']]
   if x['priority']:assert x['published']*1e9<=r['start_ns']+1000
   else:assert x['published']*1e9>=r['end_ns']-1000
 return dict(schedule=schedule,full_frozen_pages=pages,audit_groups=len(groups),timed_browser_frames=len(pub))
