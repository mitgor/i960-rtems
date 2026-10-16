#!/usr/bin/env python3
"""Verify and reassemble exact archive parts, then extract full evidence."""
import argparse,hashlib,json,tarfile,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('destination',type=Path,nargs='?');p.add_argument('--verify-only',action='store_true');a=p.parse_args();r=Path(__file__).resolve().parent
assert a.verify_only or a.destination, 'provide destination or --verify-only'
with tempfile.TemporaryDirectory() as tmp:
 candidate=Path(tmp)/'candidate.tar.gz'
 with candidate.open('wb') as out:
  for row in json.loads((r/'candidate-parts.json').read_text()):
   assert Path(row['name']).name==row['name']
   b=(r/row['name']).read_bytes();assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'];out.write(b)
 files=[candidate]+[r/n/(n+'-card.tar.gz') for n in ('a1','b1','b2','a2')]+[r/'probe-evidence.tar.gz']
 for f in files:
  checksum=r/'candidate.tar.gz.sha256' if f==candidate else Path(str(f)+'.sha256')
  assert hashlib.sha256(f.read_bytes()).hexdigest()==checksum.read_text().split()[0],f
 for f in files:
  with tarfile.open(f) as t:
   members=[m for m in t if not m.issym()]
   if not a.verify_only:t.extractall(a.destination,members=members,filter='data')
print('PASS all part/archive hashes and tar metadata'+('; extracted two builds, four full captures and the bounded scalar proof' if not a.verify_only else ''))
