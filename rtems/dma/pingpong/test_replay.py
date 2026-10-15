#!/usr/bin/env python3
"""Reject corrupted evidence independently of the live assertions."""
import argparse,json,shutil,tempfile
from pathlib import Path
from verify import verify
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args();verify(a.capture)
cases=[]
def byte(name,off):
 def edit(d):
  p=d/name;b=bytearray(p.read_bytes());b[off]^=1;p.write_bytes(b)
 return edit
for off in (0,4096,69632,73696,73700,73704,73708,73712,73720,73724):cases.append(byte('pingpong-021.bin',off))
for off in (0,4096,69632):cases.append(byte('frame-dma-005.bin',off))
def rowfile(name,edit):
 def change(d):
  p=d/name;r=[json.loads(s) for s in p.read_text().splitlines()];edit(r);p.write_text(''.join(json.dumps(s)+'\n' for s in r))
 return change
cases += [rowfile('pingpong-frames.jsonl',lambda r:r[20].update(sha256='0'*64)),rowfile('pingpong-frames.jsonl',lambda r:r.pop()),rowfile('pingpong-stalls.jsonl',lambda r:r[0].update(unchanged=False)),rowfile('pingpong-stalls.jsonl',lambda r:r[0].update(seconds=0)),rowfile('owned-journal.jsonl',lambda r:r.clear()),rowfile('pingpong-journal.jsonl',lambda r:r.pop()),rowfile('frame-journal.jsonl',lambda r:r.pop()),rowfile('frame-dma-results.jsonl',lambda r:r[0]['report'].__setitem__(13,1))]
def remove_release(r):
 for i,e in enumerate(r):
  if 'request' in e and bytes.fromhex(e['request'])[0]==4:del r[i];return
cases.append(rowfile('pingpong-journal.jsonl',remove_release))
if json.loads((a.capture/'pingpong-result.json').read_text()).get('protocol_version')==2:
 def result_edit(kind):
  def change(d):
   p=d/'pingpong-result.json';v=json.loads(p.read_text())
   if kind=='counter':v['stats'][5]=0
   else:v['protocol_version']=3
   p.write_text(json.dumps(v))
  return change
 cases.extend((result_edit('counter'),result_edit('version')))
for idx,edit in enumerate(cases):
 with tempfile.TemporaryDirectory() as d:
  dest=Path(d)/'capture';shutil.copytree(a.capture,dest);edit(dest)
  try:verify(dest)
  except (AssertionError,StopIteration,IndexError,KeyError):pass
  else:raise AssertionError(f'mutation accepted: {idx}')
print(f'PASS {len(cases)} capture/journal/ownership/STOP mutations rejected')
