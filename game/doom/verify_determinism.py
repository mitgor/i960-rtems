#!/usr/bin/env python3
"""Replay content-addressed full captures, independent of the workload runner."""
import argparse, hashlib, json, lzma, struct
from pathlib import Path

def digest(data):return hashlib.sha256(data).hexdigest()
def verify_frames(pixels,palette,trace,expected):
    assert len(trace)==len(expected)
    for i,(line,want) in enumerate(zip(trace,expected)):
        assert line[0]==i
        pix=pixels.read(64000);pal=palette.read(768)
        assert len(pix)==64000 and len(pal)==768,('short frame',i)
        assert digest(struct.pack('<II',i,line[1])+pix+pal)==want,('frame mismatch',i)
    assert pixels.read(1)==b'' and palette.read(1)==b'','trailing bytes'

def main():
 assert __debug__, "run without python -O"
 p=argparse.ArgumentParser();p.add_argument('artifacts',type=Path);a=p.parse_args();root=a.artifacts
 manifest=json.loads((root/'manifest.json').read_text())
 for path,want in manifest.items():
  assert digest((root/path).read_bytes())==want,('file hash',path)
 rows=json.loads((root/'captures.json').read_text());runs=json.loads((root/'results.json').read_text())
 assert len(rows)==len(runs)==24
 assert {(r['case'],r['repeat']) for r in runs}=={(f'{p}:{d}',r) for p in (1,2) for d in (1,2,3) for r in range(4)}
 checked=set();groups={};frames=0
 for row,run in zip(rows,runs):
  name=f"p{run['case'][0]}-demo{run['case'][-1]}-{run['repeat']}"
  assert row['name']==name
  assert run['heap_fill']==(17,85,170,255)[run['repeat']]
  assert run['frames']==2100 and run['profile']['frames']==2100 and run['profile']['pointer_bytes']==4
  assert run['profile']['failed_allocations']==0
  assert run['different_frames']==[] and run['trace_equal']
  trace=[list(map(int,s.split())) for s in (root/'runs'/name/'frames.txt').read_text().splitlines()]
  hashes=json.loads((root/'runs'/name/'sha256-frames.json').read_text())
  assert len(trace)==len(hashes)==2100
  key=(row['pixels'],row['palette'])
  if run['repeat']==0:groups[run['case']]=(key,trace,hashes)
  else:assert (key,trace,hashes)==groups[run['case']],'repeat differs'
  if key not in checked:
   with lzma.open(root/row['pixels'],'rb') as pix,lzma.open(root/row['palette'],'rb') as pal:
    verify_frames(pix,pal,trace,hashes)
   checked.add(key)
  frames+=len(trace)
 before=json.loads((root/'before-captures.json').read_text())
 changes=[];changed_fixed=[]
 with lzma.open(root/before[0]['pixels'],'rb') as old1,lzma.open(root/before[1]['pixels'],'rb') as old2,lzma.open(root/rows[0]['pixels'],'rb') as fixed:
  for i in range(2100):
   x=old1.read(64000);y=old2.read(64000);z=fixed.read(64000)
   assert len(x)==len(y)==len(z)==64000
   if x!=y:changes.append((i,sum(a!=b for a,b in zip(x,y))))
   if x!=z:changed_fixed.append((i,sum(a!=b for a,b in zip(x,z))))
  assert not old1.read(1) and not old2.read(1) and not fixed.read(1)
 assert changes==[(497,2),(1426,1),(1817,4)]
 assert len(changed_fixed)==35 and sum(n for _,n in changed_fixed)==148
 # Mutation tests use real accepted bytes and their actual expected digest.
 import io
 row=rows[0];name=row['name']
 trace=[list(map(int,s.split())) for s in (root/'runs'/name/'frames.txt').read_text().splitlines()][:1]
 hashes=json.loads((root/'runs'/name/'sha256-frames.json').read_text())[:1]
 with lzma.open(root/row['pixels'],'rb') as f:pix=f.read(64000)
 with lzma.open(root/row['palette'],'rb') as f:pal=f.read(768)
 mutations=[(bytes([pix[0]^1])+pix[1:],pal,trace),(pix,bytes([pal[0]^1])+pal[1:],trace),(pix,pal,[[0,trace[0][1]+1,trace[0][2]]]),(pix[:-1],pal,trace),(pix,pal[:-1],trace),(pix+b'x',pal,trace)]
 for x,y,t in mutations:
  try:verify_frames(io.BytesIO(x),io.BytesIO(y),t,hashes)
  except AssertionError:pass
  else:raise AssertionError('mutation accepted')
 print(json.dumps(dict(runs=len(rows),frames=frames,unique_full_captures=len(checked),mutation_rejections=len(mutations),status='pass'),indent=2))
if __name__=='__main__':main()
