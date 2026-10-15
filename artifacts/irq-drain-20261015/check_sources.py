#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('extracted',type=Path);p.add_argument('mode',choices=['masked','fixed','stress-masked','stress-fixed']);a=p.parse_args()
r=a.extracted/('project' if a.mode=='masked' else 'project-'+a.mode);root=Path(__file__).resolve().parents[2];rows=[];differences=[]
allowed=set()
if 'masked' in a.mode:allowed.add('rtems/exclusive/peer_yield.h')
if a.mode.startswith('stress-'):allowed.add('rtems/residentnet/shared_heap.inc')
for folder in ('rtems','game','loader'):
 for f in sorted((r/folder).rglob('*')):
  if f.suffix not in ('.c','.h','.inc','.S','.ld') or not f.is_file():continue
  rel=str(f.relative_to(r));digest=hashlib.sha256(f.read_bytes()).hexdigest();current=root/rel
  if current.exists() and current.read_bytes()!=f.read_bytes():differences.append(rel)
  rows.append(dict(path=rel,sha256=digest))
assert set(differences)==allowed,(differences,allowed)
print(json.dumps(dict(mode=a.mode,source_files=len(rows),intentional_differences=differences,files=rows),indent=2))
