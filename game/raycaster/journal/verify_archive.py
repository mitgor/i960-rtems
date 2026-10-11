#!/usr/bin/env python3
"""Replay all journal acceptance captures using their archived executed sources."""
import argparse,hashlib,json,subprocess,sys,tarfile,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('artifacts',type=Path);a=p.parse_args();art=a.artifacts.resolve()
assert __debug__
reports=[]
with tempfile.TemporaryDirectory(prefix='i960-journal-acceptance-') as tmp:
 root=Path(tmp)
 for name in ('card-builds.tar.gz','card-live.tar.gz'):
  with tarfile.open(art/name) as archive:archive.extractall(root,filter='data')
 for row in json.loads((art/'executed-source-manifest.json').read_text()):
  assert hashlib.sha256((root/row['path']).read_bytes()).hexdigest()==row['sha256']
 assert hashlib.sha256((root/'accepted/kernel.bin').read_bytes()).hexdigest()=='3c6f40e44f77f09f8fbed02722232d0651f4a4b7514ccb198fbaa4768dc44f4d'
 assert hashlib.sha256((root/'accepted/dac960rtems.ko').read_bytes()).hexdigest()=='3796b5cbeacb853d31c966defa0788fcd568886160725674f7d7011c77aef0fa'
 game=root/'game/raycaster';subprocess.run(['make','-B','-C',str(game),'all'],check=True,stdout=subprocess.DEVNULL)
 def run(script,*args):return json.loads(subprocess.check_output([sys.executable,str(script),*map(str,args)],text=True))
 for name in ('a1','b1','b2','a2','idle','limit','signal','disconnect','overlap'):
  cap=root/('live-'+name)
  report=run(game/'browserqueue/verify.py',cap,'--payload',root/'accepted/kernel.bin','--module',root/'accepted/dac960rtems.ko')
  assert report==json.loads((art/('verified-'+name+'.json')).read_text());reports.append(report)
  assert run(game/'upload/verify_quiet.py',cap)==json.loads((art/('quiet-'+name+'.json')).read_text())
  if name in ('a1','b1','b2','a2'):
   profile=run(game/'browserqueue/profile.py',cap,art/('browser-'+name))
   assert profile==json.loads((art/('profile-'+name+'.json')).read_text())
 assert run(Path(__file__).with_name('profile.py'),root,art)==json.loads((art/'card-comparison.json').read_text())
 print(json.dumps(dict(sessions=len(reports),replies=sum(r['replies'] for r in reports),full_audits=sum(r['full_audits'] for r in reports),targeted_slots=sum(r['targeted_slots'] for r in reports),commands=sum(r['commands'] for r in reports),restored_sessions=sum(r['restored'] for r in reports)),indent=2))
