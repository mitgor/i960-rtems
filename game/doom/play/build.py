#!/usr/bin/env python3
"""Fresh-checkout interactive Doom build. Never opens the card or programs flash."""
import argparse,hashlib,json,shutil,subprocess,tarfile,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--dma',action='store_true');p.add_argument('--pipeline',action='store_true');p.add_argument('--pingpong',action='store_true');p.add_argument('--wad-ring',action='store_true');p.add_argument('--wad-profile',action='store_true');p.add_argument('--peer-yield',action='store_true');p.add_argument('--cross',default='/home/mit/i960/tools/bin/i960-coff-');p.add_argument('--frame-profile',action='store_true');p.add_argument('--no-fnv',action='store_true');p.add_argument('--direct-frame',action='store_true');p.add_argument('--presentation-test',action='store_true');p.add_argument('--low-detail',action='store_true');p.add_argument('--runtime-detail',action='store_true');p.add_argument('--detail-test',action='store_true');p.add_argument('--cpu-profile',action='store_true');p.add_argument('--column-test',action='store_true');p.add_argument('--fast-memory',action='store_true');p.add_argument('--fast-render',action='store_true');p.add_argument('--fast-columns',action='store_true');p.add_argument('--fast-point-side',action='store_true');p.add_argument('--fixed-div-profile',action='store_true');div=p.add_mutually_exclusive_group();div.add_argument('--fast-fixed-div',dest='fast_fixed_div',action='store_true');div.add_argument('--no-fast-fixed-div',dest='fast_fixed_div',action='store_false');p.set_defaults(fast_fixed_div=None);p.add_argument('--input-trace',action='store_true');a=p.parse_args()
if a.fast_fixed_div is None:a.fast_fixed_div=True
if a.input_trace:assert not a.fixed_div_profile
if a.fixed_div_profile or a.input_trace:a.frame_profile=True
assert not (a.fast_columns and a.column_test)
if a.runtime_detail:assert a.pipeline and not (a.column_test or a.detail_test or a.presentation_test)
assert not (a.column_test and (a.detail_test or a.presentation_test))
if a.column_test:a.cpu_profile=True;a.no_fnv=True;a.direct_frame=True;a.low_detail=True
if a.detail_test:a.cpu_profile=True;a.no_fnv=True;a.direct_frame=True
if a.cpu_profile:a.frame_profile=True
if a.presentation_test:a.frame_profile=True
assert not (a.detail_test and (a.presentation_test or a.low_detail))
if a.frame_profile or a.no_fnv or a.direct_frame or a.low_detail:assert a.pipeline
if a.peer_yield:assert a.wad_profile
if a.wad_profile:assert a.wad_ring and a.frame_profile
if a.wad_ring:assert a.pingpong
if a.pingpong:assert a.pipeline
if a.pipeline:a.dma=True
r=Path(__file__).resolve().parents[3];w=a.work.resolve()
if w.exists():p.error('choose a new work directory; existing experiments are not overwritten')
for tool in ('gcc','patch','make',a.cross+'gcc',a.cross+'ld',a.cross+'objcopy'):
 if not shutil.which(tool):p.error('missing build tool: '+tool)
w.mkdir(parents=True);(w/'sources').mkdir()
def run(args,log,cwd=None):
 print('Building',log,flush=True)
 with (w/log).open('w') as f:subprocess.run(list(map(str,args)),cwd=cwd,stdout=f,stderr=subprocess.STDOUT,check=True)
for row in json.loads((r/'rtems/sources.json').read_text())['sources']:
 src=r/'artifacts/rtems-20261011/sources'/row['name'];assert hashlib.sha256(src.read_bytes()).hexdigest()==row['sha256']
 shutil.copyfile(src,w/'sources'/row['name'])
with tarfile.open(w/'sources/newlib-1.11.0.tar.gz') as f:f.extractall(w,filter='data')
newlib=w/'newlib-1.11.0';run(['patch','-p1','-i',w/'sources/newlib-1.11.0-rtems-20030605.diff'],'newlib-patch.log',newlib)
with zipfile.ZipFile(r/'artifacts/doom-m1-20261011/freedoom-0.13.0.zip') as f:
 names=[n for n in f.namelist() if n.endswith('/freedoom1.wad')];assert len(names)==1;wad=f.read(names[0])
assert hashlib.sha256(wad).hexdigest()=='7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d'
(w/'freedoom1.wad').write_bytes(wad)
archive=r/'artifacts/doom-m1-20261011/doomgeneric-source.tar.gz';doomdir='doomgeneric-e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric'
for suffix,target in [('host','host32'),('cross','i960')]:
 extra=['--sanitize'] if target=='host32' else []
 run(['python3',r/'game/doom/build.py','--work',w/f'engine-{suffix}','--archive',archive,'--target',target,'--cross',a.cross,'--newlib',newlib,'--arena-runtime','--wad-cache','--platform-runtime',*(['--wad-profile'] if a.wad_profile else []),'--startup','--checkpoints',*(['--fast-point-side'] if a.fast_point_side else ['--point-side-o0']),'--visible','--play',*(['--column-test'] if a.column_test else []),*(['--fast-render'] if a.fast_render else []),*(['--fast-columns'] if a.fast_columns else []),*(['--fixed-div-profile'] if a.fixed_div_profile else []),*(['--fast-fixed-div'] if a.fast_fixed_div else ['--no-fast-fixed-div']),*(['--input-trace'] if a.input_trace else []),*extra],f'engine-{suffix}.log')
 run(['python3',r/'game/doom/runtime/platform/build.py','--newlib',newlib,'--out',w/f'platform-{suffix}','--doom',w/f'engine-{suffix}'/doomdir,'--engine',w/f'engine-{suffix}'/target/'doom-engine.o','--target',target,'--cross',a.cross,'--startup','--checkpoints','--visible','--play',*(['--double-buffer'] if a.pipeline else []),*[flag for enabled,flag in [(a.runtime_detail,'--runtime-detail'),(a.fast_memory,'--fast-memory'),(a.wad_profile,'--wad-profile'),(a.column_test,'--column-test'),(a.frame_profile,'--frame-profile'),(a.no_fnv,'--no-fnv'),(a.direct_frame,'--direct-frame'),(a.presentation_test,'--presentation-test'),(a.low_detail,'--low-detail'),(a.detail_test,'--detail-test'),(a.cpu_profile,'--cpu-profile')] if enabled],*extra],f'platform-{suffix}.log')
run(['python3',r/'game/doom/play/test_keys.py'],'keys.log')
run(['python3',r/'game/doom/play/test_native.py','--build',w/'platform-host','--newlib',newlib,'--wad',w/'freedoom1.wad'],'native.log')
run(['python3',r/'game/doom/runtime/startup/test_abi.py','--doom',w/'engine-cross'/doomdir,'--newlib',newlib,'--out',w/'abi-proof','--cross',a.cross],'abi.log')
run(['python3',r/'game/doom/runtime/platform/pack_engine.py','--build',w/'platform-cross','--out',w/'packed','--cross',a.cross],'packed.log')
run(['python3',r/'game/doom/runtime/engine/admit.py',w/'packed','--build',w/'platform-cross','--out',w/'admission','--play','--cross',a.cross,*(['--pingpong'] if a.pingpong else [])],'admission.log')
for test in ('test_play_channel.py','test_frame_protocol.py','test_bulk_protocol.py','test_bulk_poll.py','test_play_bulk_replay.py','test_checkpoint_barriers.py','test_play_stop.py'):run(['python3',r/'rtems/residentnet'/test],test+'.log')
if a.frame_profile:run(['python3',r/'game/doom/play/test_presentation.py'],'presentation-test.log')
if a.column_test:
 run(['python3',r/'game/doom/columns/test.py'],'column-kernel-test.log')
 run(['python3',r/'rtems/residentnet/test_column_profile.py'],'column-profile-test.log')
if a.cpu_profile:
 for test in ('test_cpu_samples.py','test_detail_profile.py'):run(['python3',r/'rtems/residentnet'/test],test+'.log')
if a.pipeline:
 for test in ('rtems/residentnet/test_double_buffer.py','rtems/dma/test_pipeline_replay.py','rtems/residentnet/test_play_abort.py'):run(['python3',r/test],Path(test).name+'.log')
if a.wad_ring:
 for test in ('test_target.py','test_host.py','test_client.py','test_cache.py','test_protection.py'):
  run(['python3',r/'rtems/dma/wad_ring'/test],'wad-ring-'+test+'.log')
 shutil.copytree(w/'platform-host',w/'platform-host-ring')
 run(['python3',r/'game/doom/play/test_native.py','--build',w/'platform-host-ring','--newlib',newlib,'--wad',w/'freedoom1.wad','--wad-ring'],'native-ring.log')
if a.pingpong:
 for test in ('test_target.py','test_host.py','test_client.py','test_protection.py','test_wad_handoff.py'):run(['python3',r/'rtems/dma/pingpong'/test],'pingpong-'+test+'.log')
if a.dma:
 for test in ('test_frame_target.py','test_frame_host.py','test_frame_replay.py','test_wad_target.py','test_wad_host.py','test_wad_client.py'):run(['python3',r/'rtems/dma'/test],test+'.log')
run(['python3',r/'rtems/build.py','--work',w,'--cross',a.cross,'--profile','residentnet','--secondary-reset','--fault-owner','--extra-ram','--general-heap','--heap-shared','--queue-reclaim','--owned-mib','12','--resident-upload','--doom-heap','--doom-shared','--doom-runtime','--doom-engine',w/'admission','--wad-batch','--wad-poll','--dispatch-atomic',*(['--doom-dma'] if a.dma else []),*(['--wad-ring'] if a.wad_ring else []),*(['--wad-profile'] if a.wad_profile else []),*(['--peer-yield'] if a.peer_yield else [])],'kernel.log')
run(['python3',r/'rtems/residentnet/ram_audit.py',w/'residentnet'],'ram-audit.json')
run(['python3',r/'rtems/residentnet/build_transport.py','--payload',w/'residentnet/kernel.bin','--out',w/'residentnet-module'],'transport.log')
if a.dma:run(['python3',r/'rtems/dma/test_wad_poll.py','--generated',w/'residentnet-module/dac960auto.c'],'test_wad_poll.py.log')
run(['make','-C','/lib/modules/'+subprocess.check_output(['uname','-r'],text=True).strip()+'/build','M='+str(w/'residentnet-module'),'modules'],'module.log')
(w/'play-build.json').write_text(json.dumps(dict(fast_point_side=a.fast_point_side,input_trace=a.input_trace,fixed_div_profile=a.fixed_div_profile,fast_fixed_div=a.fast_fixed_div,runtime_detail=a.runtime_detail,fast_columns=a.fast_columns,fast_render=a.fast_render,fast_memory=a.fast_memory,peer_yield=a.peer_yield,wad_profile=a.wad_profile,wad_ring=a.wad_ring,pipeline=a.pipeline,dma=a.dma,work=str(w),repository=str(r),cross=a.cross,wad_sha256=hashlib.sha256(wad).hexdigest(),kernel_sha256=hashlib.sha256((w/'residentnet/kernel.bin').read_bytes()).hexdigest(),module_sha256=hashlib.sha256((w/'residentnet-module/dac960auto.ko').read_bytes()).hexdigest()),indent=2)+'\n')
print('Build complete. Card untouched. Run game/doom/play/run.py only on the qualified, free card.')
