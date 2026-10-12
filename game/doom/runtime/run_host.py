#!/usr/bin/env python3
"""Compare actual Doom-on-arena output against the accepted full-frame corpus."""
import argparse,hashlib,json,os,struct,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--binary',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--wads',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True);rows=[]
for phase in (1,2):
 for demo in (1,2,3):
  name=f'p{phase}-demo{demo}-0';d=(a.out/name).resolve();d.mkdir()
  cmd=[str(a.binary.resolve()),'-iwad',str(a.wads.resolve()/f'freedoom{phase}.wad'),'-mb','6','-nosound','-timedemo',f'demo{demo}']
  with (d/'output.log').open('w') as log:
   subprocess.run(cmd,cwd=d,env=dict(os.environ,HOME=str(d),DOOM_FRAMES='2100',DOOM_RAW=str(d/'frames.raw'),DOOM_PALETTE=str(d/'palette.raw'),DOOM_TRACE=str(d/'frames.txt'),DOOM_PROFILE=str(d/'profile.json'),DOOM_CACHE_PROFILE=str(d/'cache.json'),DOOM_WAD_TRACE=str(d/'wad-reads.txt')),stdout=log,stderr=log,check=True,timeout=180)
  trace=[list(map(int,s.split())) for s in (d/'frames.txt').read_text().splitlines()];assert len(trace)==2100
  expected=json.loads((a.reference/name/'sha256-frames.json').read_text());actual=[]
  with (d/'frames.raw').open('rb') as pixels,(d/'palette.raw').open('rb') as palettes:
   for i,t in enumerate(trace):
    pix=pixels.read(64000);pal=palettes.read(768);assert len(pix)==64000 and len(pal)==768 and t[0]==i
    actual.append(hashlib.sha256(struct.pack('<II',i,t[1])+pix+pal).hexdigest())
   assert not pixels.read(1) and not palettes.read(1)
  assert actual==expected,name
  (d/'sha256-frames.json').write_text(json.dumps(actual)+'\n')
  marker=[s for s in (d/'output.log').read_text().splitlines() if s.startswith('Doom arena drained;')];assert len(marker)==1
  profile=json.loads((d/'profile.json').read_text());assert profile['frames']==2100 and profile['pointer_bytes']==4 and not profile['failed_allocations']
  row=dict(case=name,frames=2100,matches_reference=True,drain=marker[0],command=cmd,profile=profile,binary_sha256=hashlib.sha256(a.binary.read_bytes()).hexdigest());
  if (d/'cache.json').exists():
   cache=json.loads((d/'cache.json').read_text());assert cache['errors']==0;row['cache']=cache
  rows.append(row)
  (a.out/'results.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,marker[0],flush=True)
  # The accepted corpus already preserves identical bytes; retain their digests.
  (d/'frames.raw').unlink();(d/'palette.raw').unlink()
