#!/usr/bin/env python3
"""Mutate captured drain reports and require full system replay rejection."""
import argparse,json,tempfile
from pathlib import Path
from verify import verify
p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('capture',type=Path);a=p.parse_args();source=a.capture.resolve();verify(a.root,source)
for case in range(4):
 with tempfile.TemporaryDirectory() as name:
  d=Path(name)
  for f in source.iterdir():
   (d/f.name).symlink_to(f,target_is_directory=f.is_dir())
  f=d/'drain-diagnostics.jsonl';rows=[json.loads(l) for l in f.read_text().splitlines()];f.unlink()
  if case==0:rows[-1]['words'][5]^=1
  elif case==1:rows.pop()
  elif case==2:rows[-1]['words'][11]=0
  else:rows[-1]['words'][1]^=1
  f.write_text(''.join(json.dumps(r)+'\n' for r in rows))
  try:verify(a.root,d)
  except AssertionError:pass
  else:raise AssertionError('accepted tamper '+str(case))
print(json.dumps(dict(rejected=4,original_unchanged=True)))
