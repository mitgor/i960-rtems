#!/usr/bin/env python3
"""Reject corrupted payload and incomplete/duplicate terminal records in real captures."""
import argparse,json,tempfile
from pathlib import Path
from verify import verify
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--wad',type=Path,required=True);a=p.parse_args()
verify(a.capture,a.wad)
for mode in ('payload','missing-final','duplicate-final'):
 with tempfile.TemporaryDirectory() as d:
  d=Path(d)
  for name in ('play-wad.json','wad-ring-results.jsonl'):(d/name).write_bytes((a.capture/name).read_bytes())
  changed=False;pending=None
  with (a.capture/'wad-ring-journal.jsonl').open() as source,(d/'wad-ring-journal.jsonl').open('w') as dest:
   for line in source:
    if mode=='payload' and not changed:
     row=json.loads(line);raw=bytearray.fromhex(row['request'])
     if int.from_bytes(raw[:4],'little')==3:
      raw[32]^=1;row['request']=raw.hex();line=json.dumps(row)+'\n';changed=True
    if pending is not None:dest.write(pending)
    pending=line
   if mode!='missing-final':dest.write(pending)
   if mode=='duplicate-final':dest.write(pending)
  try:verify(d,a.wad)
  except (AssertionError,KeyError,ValueError):pass
  else:raise AssertionError('accepted '+mode)
print(json.dumps(dict(accepted_original=True,rejected=3,cases=['payload','missing-final','duplicate-final'])))
