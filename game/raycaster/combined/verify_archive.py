#!/usr/bin/env python3
"""Replay exact combined builds, full-audit A/B evidence and frame equivalence."""
import argparse,gzip,hashlib,json,subprocess,sys,tarfile,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;GAME=HERE.parent;ROOT=GAME.parents[1]
sys.path.insert(0,str(GAME))
from combined.optimize import combined
from callback.optimize import render_fast,request_words
p=argparse.ArgumentParser();p.add_argument('artifacts',type=Path);p.add_argument('--build-only',action='store_true');a=p.parse_args();art=a.artifacts.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def call(script,*args):return json.loads(subprocess.check_output(['python3',str(script),*map(str,args)],text=True))
with tempfile.TemporaryDirectory(prefix='i960-ackpublish-replay-') as directory:
 tmp=Path(directory)
 for name in ['builds.tar.gz']+([] if a.build_only else ['live.tar.gz']):
  with tarfile.open(art/name) as t:t.extractall(tmp,filter='data')
 lines=(art/'binary-sha256.txt').read_text().splitlines();assert len(lines)==3
 assert {line.split()[1] for line in lines}=={'target/session/kernel.bin','baseline.bin','module/dac960rtems.ko'}
 for line in lines:
  digest,name=line.split();assert sha(tmp/name)==digest,name
 assert sha(tmp/'baseline.bin')=='38f9969b2177b6cfd7e471eac939f6febd9bd0498292a7544c8122b199212776'
 assert sha(tmp/'module/dac960rtems.ko')=='3796b5cbeacb853d31c966defa0788fcd568886160725674f7d7011c77aef0fa'
 source=tmp/'target/project/rtems/session';meta=json.loads((tmp/'target/session/raycaster-build.json').read_text())
 assert meta['frame_queue'] and meta['queue_combined'] and meta['request_words'] and meta['render_fast']
 for name,digest in meta['source_sha256'].items():assert sha(source/name if name!='buffer_io.h' else source.parent/'transport/buffer_io.h')==digest,name
 assert (source/'queue.c').read_text()==combined((GAME/'queue/queue.c').read_text())
 assert (source/'queue.h').read_bytes()==(GAME/'queue/queue.h').read_bytes()
 assert (source/'ray.c').read_text()==render_fast((GAME/'ray.c').read_text())
 assert (source.parent/'transport/buffer_io.h').read_text()==request_words((ROOT/'rtems/transport/buffer_io.h').read_text())
 out=tmp/'regenerated-module';subprocess.run(['python3',str(GAME/'queue/build_transport.py'),'--out',str(out),'--queue'],check=True,stdout=subprocess.DEVNULL)
 for f in out.iterdir():assert f.read_bytes()==(tmp/'module'/f.name).read_bytes(),f.name
 if a.build_only:
  print(json.dumps(dict(binary_hashes=3,target_source_manifests=1,regenerated_modules=1),indent=2));sys.exit(0)
 for name in ['queue/live.py','queue/verify.py','combined/model.py','combined/batch.py','combined/profile.py']:
  assert (tmp/'game/raycaster'/name).read_bytes()==(GAME/name).read_bytes(),name
 replies=audits=commands=slots=0;boots=set();trajectories=[]
 for name,mode in [('separate1','separate'),('combined1','combined'),('combined2','combined'),('separate2','separate')]:
  cap=tmp/('live-'+name);payload=tmp/('baseline.bin' if mode=='separate' else 'target/session/kernel.bin')
  assert json.loads((cap/'queue-test.json').read_text())['pipeline']==mode
  report=call(GAME/'queue/verify.py',cap,'--payload',payload,'--module',tmp/'module/dac960rtems.ko')
  assert report==json.loads((art/(name+'-verified.json')).read_text())
  assert call(GAME/'upload/verify_quiet.py',cap)==json.loads((art/(name+'-quiet.json')).read_text())
  replies+=report['replies'];audits+=report['full_audits'];commands+=report['commands'];slots+=report['targeted_slots'];boots.add(report['boot_id'])
  phases=json.loads((cap/'phases.json').read_text());frames=[]
  with gzip.open(cap/'full-audits.bin.gz','rb') as f:
   for row in phases:
    data=f.read(524288);assert len(data)==524288
    if row['label'] in ('steady-combined','steady-publish'):frames.append(data[0x60000+64:0x60000+64+4864])
   assert not f.read()
  assert len(frames)==80;trajectories.append(frames)
 assert all(f==trajectories[0] for f in trajectories[1:])
 assert replies==audits==586 and commands==19720 and slots==452 and len(boots)==1
 assert call(HERE/'profile.py',tmp)==json.loads((art/'comparison.json').read_text())
 sys.path.insert(0,str(ROOT/'rtems/transport'));from run import verify_close,ROM_SHA
 verify_close(tmp/'production-close')
 opened=tmp/'production-restored/open';before=(opened/'stage-before-a5.bin').read_bytes()
 assert before==(opened/'stage-before-5a.bin').read_bytes() and hashlib.sha256(before).hexdigest()==ROM_SHA
 assert json.loads((tmp/'production-restored/request.json').read_text())['boot_id']==next(iter(boots))
 assert '200 OK' in (art/'http-headers.txt').read_text() and 'Vader' in (art/'http.html').read_text()
 assert '\nactive\n' in (art/'service-state.txt').read_text()
 print(json.dumps(dict(binary_hashes=3,target_source_manifests=1,regenerated_modules=1,accepted_sessions=4,replies=replies,full_audits=audits,targeted_slots=slots,commands=commands,identical_frames_each_session=80,restorations=4,boot_id=next(iter(boots)),production_restored=True),indent=2))
