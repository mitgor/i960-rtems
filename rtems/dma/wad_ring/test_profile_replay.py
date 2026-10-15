#!/usr/bin/env python3
"""Tamper with real captured profile evidence without altering the originals."""
import argparse,json,struct,tempfile
from pathlib import Path
from verify_profile import verify
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args();source=a.capture.resolve()
verify(source);rejected=0
for case in range(6):
 with tempfile.TemporaryDirectory() as name:
  d=Path(name)
  for f in source.iterdir():
   if f.is_file():(d/f.name).symlink_to(f)
  if case<3:
   f=d/'wad-profile.json';data=json.loads(f.read_text());data['words'][[0,3,8+11*3][case]]^=1;f.unlink();f.write_text(json.dumps(data))
  elif case==3:
   f=d/'upload-journal.jsonl';rows=[json.loads(x) for x in f.read_text().splitlines()]
   for row in rows:
    q=bytes.fromhex(row['request'])
    if row['op']==1 and struct.unpack_from('<2I',q,40)==(21,8):
     rows.remove(row);break
   else:raise AssertionError('missing report request')
   f.unlink();f.write_text(''.join(json.dumps(r)+'\n' for r in rows))
  else:
   f=d/'play-0-1.bin';b=bytearray(f.read_bytes());b[64960+(0 if case==4 else 60)]^=1;f.unlink();f.write_bytes(b)
  try:verify(d)
  except (AssertionError,KeyError):rejected+=1
  else:raise AssertionError('accepted tampered profile case '+str(case))
assert rejected==6
print(json.dumps(dict(rejected_mutations=rejected,original_unchanged=True)))
