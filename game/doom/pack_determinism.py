#!/usr/bin/env python3
"""Preserve complete host output; identical compressed captures share one blob."""
import argparse,hashlib,json,lzma,shutil,tarfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('workspace',type=Path);p.add_argument('output',type=Path);a=p.parse_args();r=a.workspace.resolve();out=a.output.resolve();out.mkdir();(out/'blobs').mkdir()
def blob(path):
 if path.suffix!='.xz':
  compressed=path.with_suffix(path.suffix+'.xz')
  with path.open('rb') as src,lzma.open(compressed,'wb',preset=1) as dst:shutil.copyfileobj(src,dst)
  path=compressed
 name=hashlib.sha256(path.read_bytes()).hexdigest()+'.xz';dst=out/'blobs'/name
 if not dst.exists():shutil.copyfile(path,dst)
 return 'blobs/'+name
rows=[]
results=json.loads((r/'runs/results.json').read_text())
assert len(results)==24 and all(not x['different_frames'] and x['trace_equal'] for x in results)
for run in results:
 name=f"p{run['case'][0]}-demo{run['case'][-1]}-{run['repeat']}";d=r/'runs'/name
 dest=out/'runs'/name;dest.mkdir(parents=True)
 for path in d.iterdir():
  if path.suffix in ('.json','.txt','.log'):shutil.copyfile(path,dest/path.name)
 rows.append(dict(name=name,pixels=blob(d/'frames.raw.xz'),palette=blob(d/'palette.raw.xz')))
(out/'captures.json').write_text(json.dumps(rows,indent=2)+'\n')
shutil.copyfile(r/'runs/results.json',out/'results.json')
before=[]
for n in (1,2):
 d=r/f'before-{n}';before.append(dict(name=d.name,pixels=blob(d/'frames.raw')))
 dest=out/d.name;dest.mkdir()
 for name in ('frames.txt','profile.json','output.log'):shutil.copyfile(d/name,dest/name)
(out/'before-captures.json').write_text(json.dumps(before,indent=2)+'\n')
for pattern in ('diagnose*','watch*','before-after.json','matrix.log','test-*.log','environment.txt'):
 for path in r.glob(pattern):
  if path.is_file():shutil.copyfile(path,out/path.name)
with tarfile.open(out/'builds.tar.gz','w:gz') as tf:
 for name in ('before','after','target','tools','before-profile.c','test-columns','test-profile'):
  tf.add(r/name,arcname=name)
manifest={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(out, len(manifest),'files',sum(p.stat().st_size for p in out.rglob('*') if p.is_file()),'bytes')
