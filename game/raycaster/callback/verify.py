#!/usr/bin/env python3
"""Replay exact source/binary evidence and all eight accepted card sessions."""
import argparse,hashlib,json,math,subprocess,tarfile,tempfile
from pathlib import Path
from optimize import request_words,render_fast
HERE=Path(__file__).resolve().parent;GAME=HERE.parent;ROOT=GAME.parents[1]
p=argparse.ArgumentParser();p.add_argument('artifacts',type=Path);a=p.parse_args();art=a.artifacts.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def call(script,*args):return json.loads(subprocess.check_output(['python3',str(script),*map(str,args)],text=True))
def agree(x,y):
 if isinstance(x,dict):
  assert x.keys()==y.keys()
  for k in x:agree(x[k],y[k])
 elif isinstance(x,list):
  assert len(x)==len(y)
  for u,v in zip(x,y):agree(u,v)
 elif isinstance(x,float):assert math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-12),(x,y)
 else:assert x==y,(x,y)
with tempfile.TemporaryDirectory(prefix='i960-callback-replay-') as directory:
 tmp=Path(directory)
 with tarfile.open(art/'builds.tar.gz') as t:t.extractall(tmp,filter='data')
 manifest=(art/'binary-sha256.txt').read_text().splitlines()
 assert {line.split()[1] for line in manifest}=={'target-fast/session/kernel.bin','target-validate/session/kernel.bin','module50/dac960rtems.ko','module20/dac960rtems.ko','module-release/dac960rtems.ko'}
 assert len(manifest)==5
 for line in manifest:
  digest,name=line.split();assert sha(tmp/name)==digest,name
 for name,fast in [('target-validate',False),('target-fast',True)]:
  source=tmp/name/'project/rtems/session';meta=json.loads((tmp/name/'session/raycaster-build.json').read_text())
  for filename,digest in meta['source_sha256'].items():
   f=source/filename if filename!='buffer_io.h' else source.parent/'transport/buffer_io.h'
   assert sha(f)==digest,filename
  ray=(GAME/'ray.c').read_text();assert (source/'ray.c').read_text()==(render_fast(ray) if fast else ray)
  assert (source.parent/'transport/buffer_io.h').read_text()==request_words((ROOT/'rtems/transport/buffer_io.h').read_text())
 for module,poll20,detail in [('module50',False,True),('module20',True,True),('module-release',False,False)]:
  args=['--out',tmp/('rebuilt-'+module)]+(['--poll20'] if poll20 else [])+([] if detail else ['--coarse'])
  subprocess.run(['python3',str(HERE/'build_transport.py'),*map(str,args)],check=True,stdout=subprocess.DEVNULL)
  for f in (tmp/('rebuilt-'+module)).iterdir():assert f.read_bytes()==(tmp/module/f.name).read_bytes(),f.name
 baseline=call(HERE/'baseline.py');assert baseline==json.loads((art/'baseline-attribution.json').read_text())
 result=dict(binary_hashes_verified=5,target_source_manifests_verified=2,generated_modules_reproduced=3,baseline_profile_reproduced=True,new_card_sessions=0)
 assert (art/'live.tar.gz').exists(),'accepted live evidence missing'
 if (art/'live.tar.gz').exists():
  with tarfile.open(art/'live.tar.gz') as t:t.extractall(tmp,filter='data')
  runs=[('base1','base','module50'),('validate','validate','module50'),('fast1','fast','module50'),('poll1','fast','module20'),('poll2','fast','module20'),('fast2','fast','module50'),('base2','base','module50')]
  replies=audits=commands=0;boots=set()
  for name,target,module in runs:
   image=ROOT/'artifacts/transfer-20261011/kernel.bin' if target=='base' else tmp/('target-'+target)/'session/kernel.bin'
   cap=tmp/('live-'+name);ko=tmp/module/'dac960rtems.ko'
   boots.add(json.loads((cap/'request.json').read_text())['boot_id'])
   report=call(GAME/'verify_card.py',cap,'--payload',image,'--module',ko)
   assert report==json.loads((art/(name+'-verified.json')).read_text())
   replies+=report['verified_replies'];audits+=report['verified_full_allocation_audits']
   agree(call(GAME/'profile.py',cap/'phases.json'),json.loads((art/(name+'-profile.json')).read_text()))
   report=call(GAME/'transfer/profile.py',cap);commands+=report['commands']
   assert report==json.loads((art/(name+'-commands.json')).read_text())
   assert call(GAME/'upload/verify_quiet.py',cap)==json.loads((art/(name+'-quiet.json')).read_text())
  agree(call(HERE/'compare.py',tmp),json.loads((art/'comparison.json').read_text()))
  cap=tmp/'live-release'
  image=tmp/'target-fast/session/kernel.bin';ko=tmp/'module-release/dac960rtems.ko'
  report=call(GAME/'verify_card.py',cap,'--payload',image,'--module',ko)
  assert report==json.loads((art/'release-verified.json').read_text())
  replies+=report['verified_replies'];audits+=report['verified_full_allocation_audits']
  agree(call(GAME/'profile.py',cap/'phases.json'),json.loads((art/'release-profile.json').read_text()))
  assert call(GAME/'upload/verify_quiet.py',cap)==json.loads((art/'release-quiet.json').read_text())
  boots.add(json.loads((cap/'request.json').read_text())['boot_id']);assert len(boots)==1
  import sys
  sys.path.insert(0,str(ROOT/'rtems/transport'))
  from run import verify_close,ROM_SHA
  verify_close(tmp/'production-close')
  opened=tmp/'production-restored/open'
  before=(opened/'stage-before-a5.bin').read_bytes()
  assert before==(opened/'stage-before-5a.bin').read_bytes()
  assert hashlib.sha256(before).hexdigest()==ROM_SHA
  assert '200 OK' in (art/'http-headers.txt').read_text()
  assert 'Vader' in (art/'http.html').read_text()
  assert replies==3368 and audits==104 and commands==82810
  production=json.loads((tmp/'production-restored/request.json').read_text())
  assert production['boot_id']==next(iter(boots))
  assert '\nactive\n' in (art/'service-state.txt').read_text()
  result.update(new_card_sessions=8,replies=replies,full_audits=audits,initial_prefix_audits=8,profiled_commands=commands,restored_sessions=8,boot_id=next(iter(boots)),production_restored=True)
 print(json.dumps(result,indent=2))
