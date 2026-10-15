#!/usr/bin/env python3
"""Verify archive SHA-256 before extraction; omit absolute workspace symlinks."""
import argparse,hashlib,tarfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('destination',type=Path);a=p.parse_args();r=Path(__file__).resolve().parent
archives=[r/'candidate.tar.gz']+[r/n/(n+'-card.tar.gz') for n in ('abba','baab','fast')]
for f in archives:assert hashlib.sha256(f.read_bytes()).hexdigest()==Path(str(f)+'.sha256').read_text().split()[0],f
for f in archives:
 with tarfile.open(f) as t:t.extractall(a.destination,members=[m for m in t if not m.issym()],filter='data')
print('PASS all archive hashes; extracted sources, binaries and three complete captures')
