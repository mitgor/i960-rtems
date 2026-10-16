#!/usr/bin/env python3
"""Replay saved evidence locally against exact archived kernel/module/WAD bytes."""
import argparse,json,math,subprocess,tarfile,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--captures',type=Path,required=True);a=p.parse_args();out=Path(__file__).resolve().parent;repo=out.parents[1]
roundoff=[]
def equal(actual,expected,path):
 assert type(actual)==type(expected),path
 if isinstance(actual,dict):
  assert actual.keys()==expected.keys(),path
  for k in actual:equal(actual[k],expected[k],path+'.'+k)
 elif isinstance(actual,list):
  assert len(actual)==len(expected),path
  for i,(x,y) in enumerate(zip(actual,expected)):equal(x,y,path+'.'+str(i))
 elif isinstance(actual,float):
  assert math.isfinite(actual) and math.isfinite(expected) and math.isclose(actual,expected,rel_tol=1e-12,abs_tol=1e-10),path
  if actual!=expected:roundoff.append(dict(path=path,local=actual,remote=expected))
 else:assert actual==expected,path
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp)
 with tarfile.open(a.archive) as tf:
  selected=[]
  for m in tf:
   if m.name in {b+'/'+n for b in ('build','build-fast','build-plain') for n in ('residentnet/build.json','residentnet/kernel.bin','residentnet/kernel.symbols','residentnet-module/dac960auto.ko','freedoom1.wad')}:selected.append(m)
  assert len(selected)==15;tf.extractall(root,members=selected,filter='data')
 for run in ('p0','a1','b1','b2','a2'):
  build=root/('build-plain' if run=='p0' else ('build' if run.startswith('a') else 'build-fast'));capture=a.captures/('live-'+run)
  for key,cmd in [('system',['rtems/residentnet/verify.py','--root',build,capture]),('frames',['rtems/residentnet/verify_play_pipeline.py',capture]),('wad',['rtems/dma/wad_ring/verify.py',capture,'--wad',build/'freedoom1.wad'])]:
   result=subprocess.check_output(['python3',str(repo/cmd[0]),*map(str,cmd[1:])],text=True)
   (out/run/(run+'-local-'+key+'.json')).write_text(result)
   equal(json.loads(result),json.loads((out/run/(run+'-'+key+'.json')).read_text()),run+'.'+key)
  print(run,'PASS local system/frame/WAD replay; summary fields agree within floating roundoff',flush=True)
(out/'local-replay-roundoff.json').write_text(json.dumps(roundoff,indent=2)+'\n')
