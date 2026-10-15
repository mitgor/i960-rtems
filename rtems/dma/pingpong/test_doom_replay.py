#!/usr/bin/env python3
"""Mutate real accepted Doom captures, independently of the live reader."""
import argparse,json,shutil,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'residentnet'))
from verify_play_pipeline import verify
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args();verify(a.capture)
def byte(name,offset):
 def mutate(d):
  p=d/name;b=bytearray(p.read_bytes());b[offset]^=1;p.write_bytes(b)
 return mutate
def jsonfile(name,fn,lines=False):
 def mutate(d):
  p=d/name;v=[json.loads(x) for x in p.read_text().splitlines()] if lines else json.loads(p.read_text());fn(v);p.write_text(''.join(json.dumps(x)+'\n' for x in v) if lines else json.dumps(v))
 return mutate
cases=[byte('pingpong-021.bin',o) for o in (0,4096,68096,69632,73696,73700,73704,73708,73712,73716,73720,73724)]
cases += [byte('play-0-21.bin',100),byte('play-0-21.dfb',100),byte('frame-dma-001.bin',100)]
cases += [jsonfile('doom-pingpong-result.json',lambda v:v['stats'].__setitem__(0,0)),jsonfile('doom-pingpong-result.json',lambda v:v.update(stopped_held=[])),jsonfile('doom-pingpong-stall.json',lambda v:v.update(unchanged=False)),jsonfile('doom-pingpong-stall.json',lambda v:v.update(seconds=0)),jsonfile('play-frames.jsonl',lambda v:v[20].update(sha256='0'*64),True),jsonfile('play-frames.jsonl',lambda v:v.pop(),True),jsonfile('pingpong-journal.jsonl',lambda v:v.pop(),True),jsonfile('frame-journal.jsonl',lambda v:v.pop(),True)]
def remove_release(rows):
 for i,r in enumerate(rows):
  if bytes.fromhex(r.get('request',''))[:4]==b'\x04\0\0\0':del rows[i];return
 raise AssertionError('no release')
cases.append(jsonfile('pingpong-journal.jsonl',remove_release,True))
for i,mutate in enumerate(cases):
 with tempfile.TemporaryDirectory() as d:
  d=Path(d);shutil.copytree(a.capture,d,dirs_exist_ok=True);mutate(d)
  try:verify(d)
  except (AssertionError,IndexError,KeyError,StopIteration,ValueError):pass
  else:raise AssertionError(f'tamper {i} accepted')
print(json.dumps(dict(rejected=len(cases),accepted_original=True)))
