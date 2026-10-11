#!/usr/bin/env python3
"""Replay preserved upload A/B captures, sources, byte guards and measurements."""
import argparse,gzip,hashlib,json,math,re,subprocess,tarfile,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
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
assert sha(art/'kernel.bin')=='8a19e5a357d3443721ee835d5fbdfd52ffd61710b339b8be9d74554d947da5e3'
replies=audits=commands=quiet_logs=0;boots=set();modules={}
with tempfile.TemporaryDirectory(prefix='i960-upload-replay-') as temp:
 tmp=Path(temp)
 with tarfile.open(art/'live.tar.gz') as t:t.extractall(tmp,filter='data')
 for name,quiet,detail in [('module-base',False,True),('module-quiet',True,True),('module-release',True,False)]:
  with tarfile.open(art/name/'source.tar.gz') as t:t.extractall(tmp/'source',filter='data')
  args=['--out',tmp/name]
  if quiet:args+=['--quiet']
  if not detail:args+=['--coarse']
  subprocess.run(['python3',str(HERE/'build.py'),*map(str,args)],check=True,stdout=subprocess.DEVNULL)
  for f in (tmp/'source'/name).iterdir():
   if not f.name.endswith('.mod.c'):assert f.read_bytes()==(tmp/name/f.name).read_bytes(),f.name
  modules[name]=sha(art/name/'dac960rtems.ko')
 for run in ['base1','fast1','fast2','base2','release']:
  module='module-base' if run.startswith('base') else 'module-release' if run=='release' else 'module-quiet'
  cap=tmp/('live-'+run)
  r=call(HERE.parent/'verify_card.py',cap,'--payload',art/'kernel.bin','--module',art/module/'dac960rtems.ko')
  agree(r,json.loads((art/(run+'-verified.json')).read_text()));assert r['verified_replies']==421
  replies+=r['verified_replies'];audits+=r['verified_full_allocation_audits']
  boots.add(json.loads((cap/'request.json').read_text())['boot_id'])
  agree(call(HERE.parent/'profile.py',cap/'phases.json'),json.loads((art/(run+'-profile.json')).read_text()))
  if run!='release':
   r=call(HERE.parent/'transfer/profile.py',cap);commands+=r['commands']
   agree(r,json.loads((art/(run+'-commands.json')).read_text()))
  if not run.startswith('base'):
   r=call(HERE/'verify_quiet.py',cap);quiet_logs+=r['step_logs_checked']
   agree(r,json.loads((art/(run+'-quiet.json')).read_text()))
 for i in range(10):
  cap=tmp/('smoke-%02d'%i)
  r=call(HERE.parent/'verify_card.py',cap,'--payload',art/'kernel.bin','--module',art/'module-quiet/dac960rtems.ko','--browser')
  assert r['verified_replies']==4
  call(HERE/'verify_quiet.py',cap)
 # Preserve the first candidate's successful run and the rejected startup.
 for name,module in [('exploratory-base','module-base'),('exploratory-fast-pass','module-quiet-v1')]:
  r=call(HERE.parent/'verify_card.py',tmp/name,'--payload',art/'kernel.bin','--module',art/module/'dac960rtems.ko')
  assert r['verified_replies']==421
 call(HERE/'verify_quiet.py',tmp/'exploratory-fast-pass','--activation','open')
 assert len(boots)==1
 import sys
 sys.path.insert(0,str(ROOT/'rtems/transport'))
 from run import verify_close
 verify_close(tmp/'production-close')
 failed=tmp/'exploratory-fast-rejected';verify_close(failed/'close')
 meta=json.loads((failed/'request.json').read_text())
 assert meta['module_sha256']==sha(art/'module-quiet-v1/dac960rtems.ko')
 assert meta['payload_sha256']==sha(art/'kernel.bin')
 log=(failed/'failure-000001/result.txt').read_text()
 assert 'QUIET END:' in log and 'SESSION CLOSE rc=0 pending=0 exec-dirty=0 stage-dirty=0' in log
 prefix=log.split('QUIET END:')[0]
 assert 'status=017f' not in prefix
 # Exactly four stale PING replies before restoration started; no user callback.
 prior=prefix.split('QUIET PAIR')[1]
 assert prior.count('status=017e')==4
 last={}
 for off,k,data in re.findall(r'QUIET BYTES address=c004cec0 offset=(\d+) pass=([01]) data=([0-9a-f]+)',log):last[int(k),int(off)]=bytes.fromhex(data)
 original=(ROOT/'artifacts/vendor-fujitsu/4.07-0-29/unpacked.bin').read_bytes()[0x3cec0:0x3cf10]
 for k in [0,1]:assert b''.join(last[k,off] for off in [0,32,64])==original
 assert gzip.decompress((failed/'trace.bin.gz').read_bytes())==b''
 agree(call(HERE/'metrics.py',tmp),json.loads((art/'upload-waits.json').read_text()))
 agree(call(HERE.parent/'transfer/compare.py',art),json.loads((art/'comparison.json').read_text()))
print(json.dumps(dict(replies=replies,full_audits=audits,initial_prefix_snapshots=5,restored_sessions=5,profiled_commands=commands,smoke_sessions=10,smoke_replies=40,exploratory_replies=842,rejected_startups_restored=1,quiet_step_logs_checked=quiet_logs,all_sources_reproduced=True,all_profiles_reproduced=True,boot_id=next(iter(boots)),payload_sha256=sha(art/'kernel.bin'),modules=modules),indent=2))
