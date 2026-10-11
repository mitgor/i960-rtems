#!/usr/bin/env python3
"""Replay preserved queue builds, all accepted full audits, and HTTP recovery."""
import argparse,hashlib,json,subprocess,sys,tarfile,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;GAME=HERE.parent;ROOT=GAME.parents[1]
sys.path.insert(0,str(GAME/'callback'))
from optimize import request_words,render_fast
p=argparse.ArgumentParser();p.add_argument('artifacts',type=Path);a=p.parse_args();art=a.artifacts.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def call(script,*args):return json.loads(subprocess.check_output(['python3',str(script),*map(str,args)],text=True))
with tempfile.TemporaryDirectory(prefix='i960-queue-replay-') as directory:
 tmp=Path(directory)
 for archive in ['builds.tar.gz','corrected-build.tar.gz','live.tar.gz']:
  with tarfile.open(art/archive) as t:t.extractall(tmp,filter='data')
 for manifest,count in [('binary-sha256.txt',4),('corrected-binary-sha256.txt',1)]:
  lines=(art/manifest).read_text().splitlines();assert len(lines)==count
  for line in lines:
   digest,name=line.split();assert sha(tmp/name)==digest,name
 assert sha(tmp/'baseline.bin')=='2954a3ec444fb09e7346323f69405f95fc270efd258a2398afb81148b7663b5e'
 source=tmp/'target/project/rtems/session';meta=json.loads((tmp/'target/session/raycaster-build.json').read_text())
 assert meta['frame_queue'] and meta['request_words'] and meta['render_fast']
 for name,digest in meta['source_sha256'].items():assert sha(source/name if name!='buffer_io.h' else source.parent/'transport/buffer_io.h')==digest,name
 for name in ['queue.c','queue.h']:assert (source/name).read_bytes()==(HERE/name).read_bytes()
 assert (source/'ray.c').read_text()==render_fast((GAME/'ray.c').read_text())
 assert (source.parent/'transport/buffer_io.h').read_text()==request_words((ROOT/'rtems/transport/buffer_io.h').read_text())
 for module,queue in [('module-base',False),('module-queue-v2',True)]:
  out=tmp/('regenerated-'+module)
  subprocess.run(['python3',str(HERE/'build_transport.py'),'--out',str(out),*(['--queue'] if queue else [])],check=True,stdout=subprocess.DEVNULL)
  for f in out.iterdir():assert f.read_bytes()==(tmp/module/f.name).read_bytes(),f.name
 # Preserve the failed build as failed, and show the regression detects it.
 old=(tmp/'module-queue/dac960rtems.c').read_text();assert old.count('i < 54')==3
 failed=tmp/'failed-v1';failed.mkdir()
 with tarfile.open(art/'failed-v1.tar.gz') as t:t.extractall(failed,filter='data')
 assert sha(failed/'module-queue/dac960rtems.ko')==sha(tmp/'module-queue/dac960rtems.ko')
 assert sha(failed/'target/session/kernel.bin')==sha(tmp/'target/session/kernel.bin')
 oops=(failed/'kernel-oops.txt').read_text();assert 'memcmp' in oops and 'read_pair' in oops and 'CR2: 0000000000000000' in oops
 assert not (failed/'live-queue1/summary.json').exists()
 prior=call(HERE/'verify.py',failed/'live-base1','--payload',tmp/'baseline.bin','--module',tmp/'module-base/dac960rtems.ko')
 assert prior['replies']==prior['full_audits']==81 and prior['restored']
 runs=tmp/'acceptance-v2';replies=audits=commands=slots=0;boots=set()
 for name,queue in [('base1',False),('queue1',True),('queue2',True),('base2',False)]:
  cap=runs/('live-'+name);payload=tmp/('target/session/kernel.bin' if queue else 'baseline.bin');module=tmp/('module-queue-v2' if queue else 'module-base')/'dac960rtems.ko'
  report=call(HERE/'verify.py',cap,'--payload',payload,'--module',module)
  assert report==json.loads((art/(name+'-verified.json')).read_text())
  assert call(GAME/'upload/verify_quiet.py',cap)==json.loads((art/(name+'-quiet.json')).read_text())
  replies+=report['replies'];audits+=report['full_audits'];commands+=report['commands'];slots+=report['targeted_slots'];boots.add(report['boot_id'])
 assert replies==audits==518 and commands==16720 and slots==202 and len(boots)==1
 assert prior['boot_id'] not in boots
 assert call(HERE/'profile.py',runs)==json.loads((art/'comparison.json').read_text())
 sys.path.insert(0,str(ROOT/'rtems/transport'));from run import verify_close,ROM_SHA
 verify_close(tmp/'production-close')
 opened=tmp/'production-restored/open';before=(opened/'stage-before-a5.bin').read_bytes()
 assert before==(opened/'stage-before-5a.bin').read_bytes() and hashlib.sha256(before).hexdigest()==ROM_SHA
 assert json.loads((tmp/'production-restored/request.json').read_text())['boot_id']==next(iter(boots))
 assert '200 OK' in (art/'http-headers.txt').read_text() and 'Vader' in (art/'http.html').read_text()
 assert '\nactive\n' in (art/'service-state.txt').read_text()
 print(json.dumps(dict(binary_hashes=5,target_source_manifests=1,regenerated_modules=2,accepted_sessions=4,replies=replies,full_audits=audits,targeted_slots=slots,commands=commands,restorations=4,boot_id=next(iter(boots)),production_restored=True,failed_v1_preserved=True,pre_failure_baseline_replies=prior['replies']),indent=2))
