#!/usr/bin/env python3
"""Replay exact cache misses and group only consecutive misses in a logical read.
No speculative read-ahead or measured timing claims. Source bytes stay identical."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('--cache',type=Path,required=True);p.add_argument('--bytes',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();expected=json.loads(a.cache.read_text());rows=[tuple(map(int,s.split())) for s in a.trace.read_text().splitlines()];tags={};hits=misses=wire=0;groups=[]
for off,n,got in rows:
 assert 0<=off<=a.bytes and got==min(n,a.bytes-off);runs=[];run=[]
 for block in range(off//512,(off+got+511)//512):
  slot=block%32
  if tags.get(slot)==block:
   hits+=1
   if run:runs.append(run);run=[]
  else:
   misses+=1;wire+=min(512,a.bytes-block*512);tags[slot]=block
   if run and block!=run[-1]+1:runs.append(run);run=[]
   run.append(block)
 if run:runs.append(run)
 groups.extend(runs)
assert (len(rows),hits,misses,wire)==tuple(expected[k] for k in ('requests','hits','misses','wire_bytes'))
options=[]
for cap in (1,2,4,8,16,32):
 batches=sum((len(g)+cap-1)//cap for g in groups)
 options.append(dict(max_bytes=512*cap,requests=batches,wire_bytes=wire,reduction_percent=100*(1-batches/misses),extra_bounce_bytes=512*(cap-1)))
a.output.write_text(json.dumps(dict(logical_reads=len(rows),hits=hits,misses=misses,wire_bytes=wire,options=options,speculative_read_ahead=False,performance_measured=False),indent=2)+'\n');print('PASS: exact cache replay; coalescing preserves all wire bytes and boundaries')
