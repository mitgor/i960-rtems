#!/usr/bin/env python3
"""Replay accepted N1 evidence, including unchanged full system verifiers."""
import argparse,hashlib,json,subprocess,sys,tarfile,tempfile,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
p=argparse.ArgumentParser();p.add_argument('--directory',type=Path);p.add_argument('--wad',type=Path);a=p.parse_args()
def replay(d):
 def run(name,args):
  result=json.loads(subprocess.check_output([sys.executable,*map(str,args)],text=True))
  (HERE/(name+'-replay.json')).write_text(json.dumps(result,indent=2)+'\n')
 run('new',[REPO/'artifacts/current/accele160-doom-dma-20261017/verify.py','--case',d/'new-v2-case'])
 for name,args in [
  ('old-system',[REPO/'rtems/residentnet/verify.py','--root',d/'old-build',d/'old-run']),
  ('old-frames',[REPO/'rtems/residentnet/verify_play_pipeline.py',d/'old-run']),
  ('old-profile',[REPO/'rtems/dma/wad_ring/verify_profile.py',d/'old-run']),
  ('old-drain',[REPO/'rtems/residentnet/test_drain_replay.py','--root',d/'old-build',d/'old-run'])]:run(name,args)
 if a.wad:wad=a.wad.resolve()
 else:
  archive=REPO/'artifacts/doom-m1-20261011/freedoom-0.13.0.zip'
  with zipfile.ZipFile(archive) as z:
   names=[n for n in z.namelist() if n.endswith('/freedoom1.wad')];assert len(names)==1
   wad=d/'freedoom1.wad';wad.write_bytes(z.read(names[0]))
 assert hashlib.sha256(wad.read_bytes()).hexdigest()=='7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d'
 run('old-wad',[REPO/'rtems/dma/wad_ring/verify.py',d/'old-run','--wad',wad])
 for n in ('template.bin','relocations.bin','manifest.json'):
  assert (d/'old-build/admission'/n).read_bytes()==(d/'new-v2-case/engine'/n).read_bytes()
 assert json.loads((d/'old-run/request.json').read_text())['card']['bdf']=='0000:37:04.1'
 with tempfile.TemporaryDirectory() as td:
  td=Path(td)
  for n in range(1,33):
   (td/f'frame-{n:04d}.bin').write_bytes((d/'old-run'/f'play-0-{n}.bin').read_bytes())
  run('comparison',[REPO/'game/doom/runtime/cache_bench/compare.py',td,d/'new-v2-case/run/persist/live-frames'])
 print('PASS: exact shared engine, full system/frame/drain/profile audits and 32 matched benchmark records per card')
if a.directory:replay(a.directory)
else:
 with tempfile.TemporaryDirectory(prefix='i960-n1-replay-') as td:
  with tarfile.open(HERE/'accepted.tar.xz') as t:t.extractall(td,filter='data')
  replay(Path(td))
