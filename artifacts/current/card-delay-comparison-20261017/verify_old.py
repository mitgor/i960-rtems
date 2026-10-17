#!/usr/bin/env python3
"""Replay the old-card system/frame/drain evidence without hardware access."""
import argparse,hashlib,json,subprocess,sys,tarfile,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--wad',type=Path);a=p.parse_args()
root=Path(__file__).resolve().parent;repo=root.parents[2]
with tempfile.TemporaryDirectory(prefix='i960-old-delay-replay-') as d:
 with tarfile.open(root/'old-card-evidence.tar.xz') as t:t.extractall(d,filter='data')
 d=Path(d);run=d/'i960-card-delay-old-20261017-run';build=d/'i960-card-delay-old-20261017-evidence-build'
 checks=[('system',[str(repo/'rtems/residentnet/verify.py'),'--root',str(build),str(run)]),
         ('frames',[str(repo/'rtems/residentnet/verify_play_pipeline.py'),str(run)]),
         ('profile',[str(repo/'rtems/dma/wad_ring/verify_profile.py'),str(run)]),
         ('drain',[str(repo/'rtems/residentnet/test_drain_replay.py'),'--root',str(build),str(run)])]
 if a.wad:checks.append(('wad',[str(repo/'rtems/dma/wad_ring/verify.py'),str(run),'--wad',str(a.wad.resolve())]))
 for name,args in checks:
  report=subprocess.check_output([sys.executable,*args],text=True)
  result=json.loads(report)
  (root/f'old-card-{name}-local.json').write_text(json.dumps(result,indent=2)+'\n')
 refs=json.loads((root/'old-card-reference.json').read_text())
 frames=[json.loads(x) for x in (run/'play-frames.jsonl').read_text().splitlines()]
 assert len(frames)==len(refs)==120
 for r,ref in zip(frames,refs):
  b=(run/f"play-0-{r['frame']}.bin").read_bytes()
  assert r['frame']==ref['frame'] and len(b)==65536
  assert hashlib.sha256(b).hexdigest()==r['sha256']
  assert hashlib.sha256(b[:64768]).hexdigest()==ref['pixels_palette_sha256']
 assert json.loads((run/'request.json').read_text())['card']['bdf']=='0000:37:04.1'
 print('120 frame payloads, previous pixels/palette, full system/frame/profile/drain replay passed')
