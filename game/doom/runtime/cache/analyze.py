#!/usr/bin/env python3
"""Replay logical WAD reads; distinguish cache hits from wire-byte savings."""
import argparse,collections,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('runs',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--wads',type=Path);a=p.parse_args();rows=[]
for result in json.loads((a.runs/'results.json').read_text()):
 d=a.runs/result['case'];trace=[tuple(map(int,s.split())) for s in (d/'wad-reads.txt').read_text().splitlines()];assert len(trace)==result['cache']['requests']
 wad=Path(result['command'][2]);wad=a.wads/wad.name if a.wads else wad;file_bytes=wad.stat().st_size
 assert all(0<=off<=file_bytes and got==min(n,file_bytes-off) for off,n,got in trace)
 uncached=dict(requests=sum((got+511)//512 for _,_,got in trace),wire_bytes=sum(got for _,_,got in trace))
 options=[]
 for lines in (8,32,128,256,512):
  tags={};hits=misses=wire=0
  for off,n,got in trace:
   first=off//512;last=(off+got+511)//512
   for block in range(first,last):
    slot=block%lines
    if tags.get(slot)==block:hits+=1
    else:misses+=1;tags[slot]=block;wire+=min(512,file_bytes-block*512)
  row=dict(lines=lines,bytes=lines*512+512,hits=hits,misses=misses,wire_bytes=wire)
  if lines==32:
   assert all(row[k]==result['cache'][k] for k in ('hits','misses','wire_bytes'))
  options.append(row)
 rows.append(dict(case=result['case'],frames=result['frames'],uncached_exact_512=uncached,options=options,arena_peak=result['cache']['arena_peak'],image_reservation=result['cache']['reserved_image']))
a.output.write_text(json.dumps(rows,indent=2)+'\n');print('PASS independent cache replay for',len(rows),'cases')
