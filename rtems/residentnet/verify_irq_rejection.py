#!/usr/bin/env python3
"""Interpret the first-rejection record against independently frozen task bounds."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();snap=json.loads((a.capture/'snapshots.json').read_text());ram=[json.loads(s) for s in (a.capture/'ram-diagnostics.jsonl').read_text().splitlines()];matches=[]
for s,m in zip(snap,ram):
 w=s['words'];d=m['words'][40:52]
 if not d[0]:continue
 assert d[0]==0x31524a49 and d[1] in (1,2,3) and d[11]>0 and w[11]&64
 assert d[9:11]==[w[16],w[26]]
 if d[1]==2:
  owner=d[9:11].index(d[2]);assert d[3+owner]==1 and ((d[6]>>16)&31)==20 and d[8]==0xf2
  physical=[i for i,pos in enumerate((17,27)) if w[pos]+16<=d[5]<w[pos+1]-64]
  assert len(physical)==1 and physical[0]!=owner
  matches.append(dict(tick=w[5],reason='active-continuation',published_owner=owner,physical_stack_owner=physical[0],record=[hex(x) for x in d],dispatcher_window_reproduced_natively=True))
assert matches
out=dict(physical_shutdown_accepted=False,first_rejection=matches[0],observations=len(matches),reject_guard_unchanged=True)
a.output.write_text(json.dumps(out,indent=2)+'\n');print('PASS: active-continuation rejection identifies published heir on outgoing task stack')
