#!/usr/bin/env python3
"""Synthetic wire fixtures exercise strict parsing, not hardware acceptance."""
import copy,hashlib,json,struct,tempfile
from pathlib import Path
from checkpoint_replay import check,describe,MAGIC
rows=[[MAGIC,1,4,1,0,0,0,0],[MAGIC,2,4,37,100,200,300,4671]]
def event(index,row):
 return dict(op=7,request=(struct.pack('<9I',7,42,4,0,0,0,0,0,index)+bytes(1020)).hex(),response=(struct.pack('<8I',7,42,32,1,0,0,0,0)+struct.pack('<8I',*row)+bytes(992)).hex())
base=[event(1,rows[0]),event(2,[MAGIC,0,1,0,0,0,0,0]),event(2,rows[1])]
with tempfile.TemporaryDirectory() as d:
 p=Path(d);b=p/'build';b.mkdir();c=p/'capture';c.mkdir()
 raw=b''.join(struct.pack('<8I',*r[:2],1,*r[3:]) for r in rows)
 (b/'startup-checkpoints.bin').write_bytes(raw);(b/'manifest.json').write_text(json.dumps(dict(startup=dict(checkpoints_sha256=hashlib.sha256(raw).hexdigest()))))
 def run(events,flat):
  (c/'engine-checkpoint-journal.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events));(c/'startup-checkpoints.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in flat));return check(c,b)
 r=run(base,rows);assert not r['accepted'] and r['validated_records']==2 and r['comparisons'][0]['matching_prefix']==2
 for key,offset in [('request',32),('request',4),('request',8),('request',36),('response',12),('response',8),('response',64),('response',36)]:
  e=copy.deepcopy(base);v=bytearray.fromhex(e[0][key]);v[offset]^=1;e[0][key]=v.hex()
  try:run(e,rows)
  except AssertionError:pass
  else:raise AssertionError((key,offset,'tamper accepted'))
 for e,flat in [(base,rows[:-1]),([base[0],*base],rows),(base[1:],rows)]:
  try:run(e,flat)
  except AssertionError:pass
  else:raise AssertionError('missing/duplicate evidence accepted')
 changed=copy.deepcopy(rows);changed[1][4]^=1;e=[*base[:-1],event(2,changed[1])];r=run(e,changed)
 assert not r['accepted'] and r['comparisons'][0]['matching_prefix']==1 and r['comparisons'][0]['first_difference']['card']['stage']=='player position/angle'
print('PASS 11 checkpoint wire/sequence/padding mutations rejected; honest scalar divergence localized without acceptance')

assert describe([MAGIC,51,4,38,4292935680,0,0,4674])["view_height_map_units"] == -31
assert describe([MAGIC,51,1,38,2686976,0,0,4674])["view_height_map_units"] == 41
