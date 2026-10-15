#!/usr/bin/env python3
"""Verify both archives before extracting; omit workspace symlinks."""
import argparse,hashlib,json,tarfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('mode',choices=['masked','fixed','stress-masked','stress-fixed']);p.add_argument('destination',type=Path);a=p.parse_args();root=Path(__file__).resolve().parent/a.mode;rows=[]
for kind in ('candidate','card'):
 f=root/(a.mode+'-'+kind+'.tar.gz');digest=hashlib.sha256(f.read_bytes()).hexdigest()
 assert digest==Path(str(f)+'.sha256').read_text().split()[0]
 rows.append(dict(file=f.name,sha256=digest))
a.destination.mkdir(parents=True,exist_ok=True)
for row in rows:
 with tarfile.open(root/row['file']) as t:t.extractall(a.destination,members=[m for m in t if not m.issym()],filter='data')
print(json.dumps(rows,indent=2))
