#!/usr/bin/env python3
"""Restore the newly preserved (previously untracked) bytes into a NEW directory."""
import argparse,gzip,hashlib,json,os,shutil,tarfile,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('destination',type=Path);a=p.parse_args();out=Path(__file__).resolve().parent
rows=[json.loads(x) for x in gzip.open(out/'files.jsonl.gz','rt')]
missing={}
for r in rows:
 if r['kind']=='file' and r['git_source'] is None:missing.setdefault(r['sha256'],[]).append(r)
parts=json.loads((out/'recovery-parts.json').read_text());dest=a.destination.resolve();assert not dest.exists(),'Choose a new destination'
with tempfile.TemporaryDirectory() as tmp:
 archive=Path(tmp)/'missing.tar.gz';whole=hashlib.sha256()
 with archive.open('wb') as f:
  for row in parts['parts']:
   assert Path(row['name']).name==row['name'];h=hashlib.sha256();n=0
   with (out/row['name']).open('rb') as inp:
    while True:
     b=inp.read(1024*1024)
     if not b:break
     h.update(b);whole.update(b);n+=len(b);f.write(b)
   assert h.hexdigest()==row['sha256'] and n==row['size']
 assert whole.hexdigest()==parts['archive_sha256'];dest.mkdir(parents=True)
 seen=set();count=0
 with tarfile.open(archive,'r|gz') as t:
  for m in t:
   assert m.isfile() and m.name.startswith('sha256/');sha=m.name.split('/')[1];assert sha in missing and sha not in seen
   payload=Path(tmp)/'payload';h=hashlib.sha256();n=0
   with t.extractfile(m) as inp,payload.open('wb') as f:
    while True:
     b=inp.read(1024*1024)
     if not b:break
     f.write(b);h.update(b);n+=len(b)
   assert h.hexdigest()==sha
   for r in missing[sha]:
    assert n==r['size'];rel=Path(r['path']).relative_to('/private/tmp');assert '..' not in rel.parts
    target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists()
    shutil.copyfile(payload,target);target.chmod(r['mode']);os.utime(target,ns=(r['mtime_ns'],r['mtime_ns']));count+=1
   seen.add(sha)
 assert seen==missing.keys()
 # All link definitions and directory metadata remain in files.jsonl.gz;
 # deliberately do not activate old absolute symlinks during a byte recovery.
print('Verified and restored',count,'files from',len(seen),'unique payloads into',dest)
