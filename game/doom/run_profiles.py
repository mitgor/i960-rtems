#!/usr/bin/env python3
"""Isolated read-only IWAD workload matrix; host timings are not card FPS."""
import argparse,hashlib,json,os,subprocess,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();root=a.root.resolve()
wadzip=root/'freedoom-0.13.0.zip'
assert hashlib.sha256(wadzip.read_bytes()).hexdigest()=='3f9b264f3e3ce503b4fb7f6bdcb1f419d93c7b546f4df3e874dd878db9688f59'
with zipfile.ZipFile(wadzip) as z:z.extractall(root)
cases=[]
for phase in (1,2):
 for demo in (1,2,3):cases.append((f'p{phase}-demo{demo}-6',phase,6,['-timedemo',f'demo{demo}']))
for phase,levels in [(1,[(1,1),(2,8),(3,8),(4,1)]),(2,[(1,),(15,),(30,)])]:
 for level in levels:cases.append((f'p{phase}-warp'+ '-'.join(map(str,level))+'-6',phase,6,['-warp',*map(str,level)]))
for mb in (2,3,4):
 for phase in (1,2):cases.append((f'p{phase}-demo1-{mb}',phase,mb,['-timedemo','demo1']))
cases.append(('p1-demo1-6-repeat',1,6,['-timedemo','demo1']))
reports=[]
for name,phase,mb,options in cases:
 out=root/'runs'/name;out.mkdir(parents=True,exist_ok=False)
 command=[str(root/'native/host32/doom-profile'),'-iwad',str(root/f'freedoom-0.13.0/freedoom{phase}.wad'),'-mb',str(mb),'-nosound',*options]
 with (out/'output.log').open('w') as log:
  try:r=subprocess.run(command,cwd=out,env=dict(os.environ,DOOM_PROFILE=str(out/'profile.json'),DOOM_FRAMES='2100',HOME=str(out)),stdout=log,stderr=log,timeout=90);code=r.returncode
  except subprocess.TimeoutExpired:code='timeout'
 row=dict(name=name,phase=phase,mb=mb,command=command,returncode=code)
 if (out/'profile.json').exists():row['profile']=json.loads((out/'profile.json').read_text())
 (out/'run.json').write_text(json.dumps(row,indent=2)+'\n');reports.append(row)
 (root/'profiles.json').write_text(json.dumps(reports,indent=2)+'\n')
 print(name,code,row.get('profile',{}).get('frames'),flush=True)
