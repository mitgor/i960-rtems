#!/usr/bin/env python3
"""Verify archived target/module identities, all replies, commands and profiles."""
import argparse,hashlib,json,math,subprocess,tarfile,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
p=argparse.ArgumentParser();p.add_argument('artifacts',type=Path);a=p.parse_args();art=a.artifacts.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(art/'kernel.bin')=='8a19e5a357d3443721ee835d5fbdfd52ffd61710b339b8be9d74554d947da5e3'
def agree(x,y):
 if isinstance(x,dict):
  assert x.keys()==y.keys()
  for k in x:agree(x[k],y[k])
 elif isinstance(x,list):
  assert len(x)==len(y)
  for u,v in zip(x,y):agree(u,v)
 elif isinstance(x,float):assert math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-12),(x,y)
 else:assert x==y,(x,y)
def call(script,*args):return json.loads(subprocess.check_output(['python3',str(script),*map(str,args)],text=True))
replies=audits=commands=0;boots=set();modules={}
with tempfile.TemporaryDirectory(prefix='i960-transfer-replay-') as tmp:
 tmp=Path(tmp)
 with tarfile.open(art/'live.tar.gz') as t:t.extractall(tmp,filter='data')
 for name in ['module-base','module-fast-v2','module-release']:
  with tarfile.open(art/name/'source.tar.gz') as t:t.extractall(tmp/'source',filter='data')
  modules[name]=sha(art/name/'dac960rtems.ko')
 baseline=tmp/'source/module-base';fast=tmp/'source/module-fast-v2'
 b=(baseline/'dac960rtems.c').read_text();start=b.index('static unsigned int changed(');end=b.index('static int issue_inner(',start)
 assert (fast/'dac960rtems.c').read_text()==b[:start]+(HERE/'count.h').read_text()+'\n'+b[end:]
 b=(baseline/'buffer_io.h').read_text();start=b.index('static inline int bio_response_valid(')
 assert (fast/'buffer_io.h').read_text()==b[:start]+(HERE/'validate.h').read_text()+'\n#endif\n'
 for f in baseline.iterdir():
  if f.name not in ['dac960rtems.c','buffer_io.h'] and not f.name.endswith('.mod.c'):assert f.read_bytes()==(fast/f.name).read_bytes(),f.name
 subprocess.run(['python3',str(HERE/'build.py'),'--out',str(tmp/'generated'),'--fast','--coarse'],check=True,stdout=subprocess.DEVNULL)
 for f in (tmp/'source/module-release').iterdir():
  if not f.name.endswith('.mod.c'):assert f.read_bytes()==(tmp/'generated'/f.name).read_bytes(),f.name
 for run in ['base1','fast1','fast2','base2','release']:
  module='module-base' if run.startswith('base') else 'module-release' if run=='release' else 'module-fast-v2'
  capture=tmp/('live-'+run)
  r=call(HERE.parent/'verify_card.py',capture,'--payload',art/'kernel.bin','--module',art/module/'dac960rtems.ko')
  assert r==json.loads((art/(run+'-verified.json')).read_text())
  assert r['verified_replies']==421
  replies+=r['verified_replies'];audits+=r['verified_full_allocation_audits']
  boots.add(json.loads((capture/'request.json').read_text())['boot_id'])
  agree(call(HERE.parent/'profile.py',capture/'phases.json'),json.loads((art/(run+'-profile.json')).read_text()))
  if run!='release':
   report=call(HERE/'profile.py',capture);commands+=report['commands']
   agree(report,json.loads((art/(run+'-commands.json')).read_text()))
 # Original service close must restore the known full image too.
 import sys
 sys.path.insert(0,str(ROOT/'rtems/transport'))
 from run import verify_close
 verify_close(tmp/'production-close')
 assert len(boots)==1
 agree(call(HERE/'compare.py',art),json.loads((art/'comparison.json').read_text()))
print(json.dumps(dict(replies=replies,full_audits=audits,initial_prefix_snapshots=5,restored_sessions=5,profiled_commands=commands,boot_id=next(iter(boots)),payload_sha256=sha(art/'kernel.bin'),module_sha256=modules,source_delta_verified=True,release_source_reproduced=True,all_profiles_reproduced=True,float_tolerance=1e-12),indent=2))
