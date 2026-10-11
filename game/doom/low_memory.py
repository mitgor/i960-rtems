#!/usr/bin/env python3
"""Record explicit small-zone failures separately from the baseline workload suite."""
import argparse,json,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();root=a.root.resolve();rows=[]
for name,phase,mb,args in [('p1-demo1-1',1,1,['-timedemo','demo1']),('p2-demo1-1',2,1,['-timedemo','demo1']),('p1-demo3-2',1,2,['-timedemo','demo3']),('p2-map15-2',2,2,['-warp','15'])]:
 out=root/'low-memory'/name;out.mkdir(parents=True,exist_ok=False)
 command=[str(root/'native/host32/doom-profile'),'-iwad',str(root/f'freedoom-0.13.0/freedoom{phase}.wad'),'-mb',str(mb),'-nosound',*args]
 with (out/'output.log').open('w') as f:
  try:r=subprocess.run(command,cwd=out,env=dict(os.environ,HOME=str(out),DOOM_PROFILE=str(out/'profile.json'),DOOM_FRAMES='2100'),stdout=f,stderr=f,timeout=90);code=r.returncode
  except subprocess.TimeoutExpired:code='timeout'
 row=dict(name=name,returncode=code,command=command,profile=json.loads((out/'profile.json').read_text()) if (out/'profile.json').exists() else None)
 (out/'run.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row)
(root/'low-memory.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
