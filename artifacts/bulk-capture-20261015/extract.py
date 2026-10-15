#!/usr/bin/env python3
"""Verify and unpack exact tested sources/binaries/captures; omit workspace links."""
import argparse,hashlib,tarfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('destination',type=Path);a=p.parse_args();r=Path(__file__).resolve().parent
for line in (r/'archives.sha256').read_text().splitlines():
 digest,name=line.split();assert hashlib.sha256((r/name).read_bytes()).hexdigest()==digest
for name in ('candidate.tar.gz','card.tar.gz'):
 with tarfile.open(r/name) as t:t.extractall(a.destination,members=[m for m in t if not m.issym()],filter='data')
print('PASS both archive hashes; extracted regular files')
