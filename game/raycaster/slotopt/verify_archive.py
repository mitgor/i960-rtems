#!/usr/bin/env python3
"""Exact source/binary proof and complete audited replay of the fifteen-step batch."""
import argparse,gzip,hashlib,json,math,subprocess,sys,tarfile,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;GAME=HERE.parent;ROOT=GAME.parents[1]
sys.path.insert(0,str(GAME))
from slotopt.optimize import header,diagnostic
from combined.optimize import combined
from callback.optimize import render_fast,request_words
p=argparse.ArgumentParser();p.add_argument('artifacts',type=Path);p.add_argument('--build-only',action='store_true');a=p.parse_args();art=a.artifacts.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def call(script,*args):return json.loads(subprocess.check_output(['python3',str(script),*map(str,args)],text=True))
def agree(a,b):
 if isinstance(a,dict):
  assert a.keys()==b.keys()
  for k in a:agree(a[k],b[k])
 elif isinstance(a,list):
  assert len(a)==len(b)
  for x,y in zip(a,b):agree(x,y)
 elif isinstance(a,float):assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12),(a,b)
 else:assert a==b,(a,b)
with tempfile.TemporaryDirectory(prefix='i960-slotopt-replay-') as directory:
 tmp=Path(directory)
 for name in ['builds.tar.gz']+([] if a.build_only else ['bench-live.tar.gz','release-live.tar.gz','stress-live.tar.gz']):
  with tarfile.open(art/name) as t:t.extractall(tmp,filter='data')
 lines=(art/'binary-sha256.txt').read_text().splitlines();assert len(lines)==7
 assert {line.split()[1] for line in lines}=={'baseline.bin','module/dac960rtems.ko',*[f'target-{n}/session/kernel.bin' for n in ['bench-byte','bench-hash','bench-words','hash','words']]}
 for line in lines:
  digest,name=line.split();assert sha(tmp/name)==digest,name
 assert sha(tmp/'baseline.bin')=='cd46d47e7e4fc02b68c12ee2a7046da4db7f861e90c71310ad29c61735d61c19'
 assert sha(tmp/'module/dac960rtems.ko')=='3796b5cbeacb853d31c966defa0788fcd568886160725674f7d7011c77aef0fa'
 targets=[('bench-byte','byte',True),('bench-hash','hash',True),('bench-words','words',True),('hash','hash',False),('words','words',False)]
 for name,mode,diag in targets:
  source=tmp/('target-'+name)/'project/rtems/session';meta=json.loads((tmp/('target-'+name)/'session/raycaster-build.json').read_text())
  assert meta['queue_diagnostic']==diag and meta['queue_slots']==mode and meta['queue_combined'] and meta['frame_queue']
  for filename,digest in meta['source_sha256'].items():assert sha(source/filename if filename!='buffer_io.h' else source.parent/'transport/buffer_io.h')==digest,filename
  q=combined((GAME/'queue/queue.c').read_text());assert (source/'queue.c').read_text()==(diagnostic(q) if diag else q)
  assert (source/'queue.h').read_text()==header((GAME/'queue/queue.h').read_text(),mode)
  assert (source/'ray.c').read_text()==render_fast((GAME/'ray.c').read_text())
  assert (source.parent/'transport/buffer_io.h').read_text()==request_words((ROOT/'rtems/transport/buffer_io.h').read_text())
  assert 'ASSERT(. <= 0xc0f8c000,' in (source/'link.ld').read_text()
 out=tmp/'regenerated-module';subprocess.run(['python3',str(GAME/'queue/build_transport.py'),'--out',str(out),'--queue'],check=True,stdout=subprocess.DEVNULL)
 for f in out.iterdir():assert f.read_bytes()==(tmp/'module'/f.name).read_bytes(),f.name
 report=dict(binary_hashes=7,target_source_manifests=5,unchanged_kernel_module=True)
 if a.build_only:print(json.dumps(report,indent=2));sys.exit(0)
 for name in ['slotopt/run.py','slotopt/model.py','slotopt/batch.py','slotopt/profile.py','queue/live.py','queue/verify.py']:
  assert (tmp/'game/raycaster'/name).read_bytes()==(GAME/name).read_bytes(),name
 selected=json.loads((art/'selected.json').read_text())['selected'];assert selected in ('hash','words')
 runs=[('bench-'+m,'bench-'+m) for m in ['byte','hash','words']]+[(n,t) for n,t in [('base1','base'),('hash1','hash'),('words1','words'),('words2','words'),('hash2','hash'),('base2','base'),('stress',selected)]]
 replies=audits=commands=slots=0;boots=set();frames=[]
 for name,target in runs:
  cap=tmp/('live-'+name);payload=tmp/('baseline.bin' if target=='base' else 'target-'+target+'/session/kernel.bin')
  r=call(HERE/'run.py','--verify',cap,'--payload',payload,'--module',tmp/'module/dac960rtems.ko')
  assert r==json.loads((art/(name+'-verified.json')).read_text())
  assert call(GAME/'upload/verify_quiet.py',cap)==json.loads((art/(name+'-quiet.json')).read_text())
  replies+=r['replies'];audits+=r['full_audits'];commands+=r['commands'];slots+=r['targeted_slots'];boots.add(r['boot_id'])
  if name=='stress':assert json.loads((cap/'phases.json').read_text())[-1]['mask']==3
  if name in ['base1','hash1','words1','words2','hash2','base2']:
   trajectory=[]
   with gzip.open(cap/'full-audits.bin.gz','rb') as f:
    for row in json.loads((cap/'phases.json').read_text()):
     data=f.read(524288);assert len(data)==524288
     if row['label']=='steady-combined':trajectory.append(data[0x60000+64:0x60000+64+4864])
    assert not f.read()
   assert len(trajectory)==80;frames.append(trajectory)
 assert all(frame==frames[0] for frame in frames) and replies==audits==1691 and commands==59284 and slots==2506 and len(boots)==1
 profile=call(HERE/'profile.py',tmp);agree(profile,json.loads((art/'comparison.json').read_text()))
 assert selected==min(('hash','words'),key=lambda n:profile['release'][n]['median_ms']['kernel_ms'])
 assert profile['release'][selected]['median_ms']['kernel_ms']<profile['release']['base']['median_ms']['kernel_ms']
 sys.path.insert(0,str(ROOT/'rtems/transport'));from run import verify_close,ROM_SHA
 verify_close(tmp/'production-close');opened=tmp/'production-restored/open';before=(opened/'stage-before-a5.bin').read_bytes()
 assert before==(opened/'stage-before-5a.bin').read_bytes() and hashlib.sha256(before).hexdigest()==ROM_SHA
 assert json.loads((tmp/'production-restored/request.json').read_text())['boot_id']==next(iter(boots))
 assert '200 OK' in (art/'http-headers.txt').read_text() and 'Vader' in (art/'http.html').read_text() and '\nactive\n' in (art/'service-state.txt').read_text()
 report.update(sessions=10,replies=replies,full_audits=audits,targeted_slots=slots,commands=commands,identical_release_frames=80,restorations=10,selected=selected,boot_id=next(iter(boots)),production_restored=True)
 print(json.dumps(report,indent=2))
