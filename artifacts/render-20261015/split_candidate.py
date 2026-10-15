#!/usr/bin/env python3
"""Keep each Git blob bounded; preserve the exact verified candidate archive."""
import hashlib,json
from pathlib import Path
r=Path(__file__).resolve().parent;src=r/'candidate.tar.gz';parts=[]
assert hashlib.sha256(src.read_bytes()).hexdigest()==(r/'candidate.tar.gz.sha256').read_text().split()[0]
with src.open('rb') as f:
 while b:=f.read(80*1024*1024):
  p=r/('candidate.tar.gz.part-%02d'%len(parts));p.write_bytes(b)
  parts.append(dict(name=p.name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
(r/'candidate-parts.json').write_text(json.dumps(parts,indent=2)+'\n')
print('Verified archive split into',len(parts),'pieces; retain the full archive outside Git')
