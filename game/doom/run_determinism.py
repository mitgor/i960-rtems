#!/usr/bin/env python3
"""Full byte comparisons under four heap fills. Runs only a host executable."""
import argparse, hashlib, json, lzma, os, struct, subprocess
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--root',type=Path,required=True)
p.add_argument('--binary',type=Path,required=True)
p.add_argument('--wad-dir',type=Path,required=True)
p.add_argument('--frames',type=int,default=2100)
p.add_argument('--cases',default='1:1,1:2,1:3,2:1,2:2,2:3')
a=p.parse_args();root=a.root.resolve();root.mkdir(parents=True,exist_ok=True)
binary=a.binary.resolve();reports=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for case in a.cases.split(','):
 phase,demo=map(int,case.split(':'));base=None
 for repeat,fill in enumerate((17,85,170,255)):
  d=root/f'p{phase}-demo{demo}-{repeat}';d.mkdir()
  wad=a.wad_dir.resolve()/f'freedoom{phase}.wad'
  command=[str(binary),'-iwad',str(wad),'-mb','6','-nosound','-timedemo',f'demo{demo}']
  env=dict(os.environ,HOME=str(d),MALLOC_PERTURB_=str(fill),DOOM_FRAMES=str(a.frames),DOOM_RAW=str(d/'frames.raw'),DOOM_PALETTE=str(d/'palette.raw'),DOOM_TRACE=str(d/'frames.txt'),DOOM_PROFILE=str(d/'profile.json'))
  with (d/'output.log').open('w') as log:
   r=subprocess.run(command,cwd=d,env=env,stdout=log,stderr=log,timeout=180)
  assert r.returncode==0,(d,r.returncode)
  profile=json.loads((d/'profile.json').read_text());assert profile['frames']==a.frames
  assert profile['pointer_bytes']==4 and profile['failed_allocations']==0
  trace=[list(map(int,s.split())) for s in (d/'frames.txt').read_text().splitlines()]
  assert len(trace)==a.frames and [t[0] for t in trace]==list(range(a.frames))
  assert (d/'frames.raw').stat().st_size==a.frames*64000
  assert (d/'palette.raw').stat().st_size==a.frames*768
  hashes=[];different=[]
  with (d/'frames.raw').open('rb') as pixels,(d/'palette.raw').open('rb') as palettes:
   if base: bp=(base/'frames.raw').open('rb');bc=(base/'palette.raw').open('rb')
   for i,t in enumerate(trace):
    pix=pixels.read(64000);pal=palettes.read(768)
    hashes.append(hashlib.sha256(struct.pack('<II',t[0],t[1])+pix+pal).hexdigest())
    if base:
     oldpix=bp.read(64000);oldpal=bc.read(768)
     if pix!=oldpix or pal!=oldpal:different.append(i)
   if base:bp.close();bc.close()
  # Compare timing and hashes too; full bytes above are the primary comparison.
  trace_equal=not base or (d/'frames.txt').read_bytes()==(base/'frames.txt').read_bytes()
  (d/'sha256-frames.json').write_text(json.dumps(hashes)+'\n')
  row=dict(case=case,repeat=repeat,heap_fill=fill,frames=a.frames,command=command,binary_sha256=sha(binary),wad_sha256=sha(wad),different_frames=different,trace_equal=trace_equal,profile=profile)
  (d/'run.json').write_text(json.dumps(row,indent=2)+'\n');reports.append(row)
  (root/'results.json').write_text(json.dumps(reports,indent=2)+'\n')
  print(d.name,'differing frames',different,'trace equal',trace_equal,flush=True)
  if not base:base=d
  else:
   # Retain every byte in compressed form, including failures.
   for name in ('frames.raw','palette.raw'):
    with (d/name).open('rb') as f,lzma.open(d/(name+'.xz'),'wb',preset=1) as out:
     while block:=f.read(1024*1024):out.write(block)
    (d/name).unlink()
 for name in ('frames.raw','palette.raw'):
  with (base/name).open('rb') as f,lzma.open(base/(name+'.xz'),'wb',preset=1) as out:
   while block:=f.read(1024*1024):out.write(block)
  (base/name).unlink()
assert all(not r['different_frames'] and r['trace_equal'] for r in reports),'nondeterministic output'
