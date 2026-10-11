#!/usr/bin/env python3
"""Replay all saved word-memory sessions and reproduce differential profiles."""
import argparse,hashlib,json,math,subprocess,tarfile,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('artifacts',type=Path);a=p.parse_args()
root=Path(__file__).resolve().parents[2];art=a.artifacts.resolve()
subprocess.run(['python3',str(root/'rtems/memory/verify_build.py'),str(art)],check=True,stdout=subprocess.DEVNULL)
def close(actual,saved):
 if isinstance(actual,dict):
  assert actual.keys()==saved.keys()
  for k in actual:close(actual[k],saved[k])
 elif isinstance(actual,list):
  assert len(actual)==len(saved)
  for x,y in zip(actual,saved):close(x,y)
 elif isinstance(actual,float):assert math.isclose(actual,saved,rel_tol=1e-12,abs_tol=1e-12),(actual,saved)
 else:assert actual==saved,(actual,saved)
records={};boots=set()
with tempfile.TemporaryDirectory(prefix='i960-word-replay-') as tmp:
 tmp=Path(tmp)
 with tarfile.open(art/'live.tar.gz') as t:t.extractall(tmp,filter='data')
 for run,variant in [('check','check'),('byte1','byte'),('word1','word'),('word2','word'),('byte2','byte')]:
  capture=tmp/('live-'+run)
  result=json.loads(subprocess.check_output(['python3',str(root/'game/raycaster/verify_card.py'),str(capture),'--payload',str(art/variant/'kernel.bin'),'--module',str(art/'dac960rtems.ko')],text=True))
  saved='live-check-verified.json' if run=='check' else run+'-verified.json'
  assert result==json.loads((art/saved).read_text())
  assert result['verified_replies']==421
  records[run]=result
  boots.add(json.loads((capture/'request.json').read_text())['boot_id'])
  if run!='check':
   profile=json.loads(subprocess.check_output(['python3',str(root/'game/raycaster/profile.py'),str(capture/'phases.json')],text=True))
   close(profile,json.loads((art/(run+'-profile.json')).read_text()))
 comparison=json.loads(subprocess.check_output(['python3',str(root/'game/raycaster/compare.py'),'--byte',str(art/'byte1-profile.json'),str(art/'byte2-profile.json'),'--word',str(art/'word1-profile.json'),str(art/'word2-profile.json')],text=True))
 close(comparison,json.loads((art/'comparison.json').read_text()))
assert records['check']['verified_replies']>=264
assert len(boots)==1
assert hashlib.sha256((art/'dac960rtems.ko').read_bytes()).digest()==hashlib.sha256((root/'artifacts/raycaster-20261011/dac960rtems.ko').read_bytes()).digest()
print(json.dumps(dict(sessions=records,total_replies=sum(v['verified_replies'] for v in records.values()),total_full_audits=sum(v['verified_full_allocation_audits'] for v in records.values()),native_match=True,all_profiles_reproduced=True,comparison_reproduced=True,unchanged_module=True,boot_id=next(iter(boots)),analysis_float_tolerance=1e-12),indent=2))
