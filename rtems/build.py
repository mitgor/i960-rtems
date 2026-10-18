#!/usr/bin/env python3
"""Build RTEMS 4.6.6 Classic core for a bounded DAC960 callback experiment."""
from pathlib import Path
import argparse,subprocess,shutil,json,hashlib
from lwip_patches import apply as patch_lwip
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from card_profiles import require_workflow
p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--card-profile',default=None);p.add_argument('--profile',choices=['bounded','accele160','session','net','irq','auto','autonet','mu','muctl','irqctx','muctx','switch','defer','mustop','stopcases','contain','containcases','ownership','ownirq','persistirq','leaseirq','handoff','exclusive','residentnet'],default='bounded');p.add_argument('--cross',default='/home/mit/i960/tools/bin/i960-coff-');p.add_argument("--secondary-reset",action="store_true");p.add_argument("--fault-owner",action="store_true");p.add_argument("--fault-test",type=int,choices=(0,1,2,3),default=0);p.add_argument("--extra-ram",action="store_true");p.add_argument("--general-heap",action="store_true");p.add_argument("--heap-test",type=int,choices=(0,1,2,3,4,5,6),default=0);p.add_argument("--heap-shared",action="store_true");p.add_argument("--queue-reclaim",action="store_true");p.add_argument("--owned-mib",type=int,choices=(0,1,4,10,12),default=0);p.add_argument("--resident-upload",action="store_true");p.add_argument('--doom-heap',action='store_true');p.add_argument('--doom-shared',action='store_true');p.add_argument('--doom-runtime',action='store_true');p.add_argument('--doom-engine',type=Path);p.add_argument('--wad-batch',action='store_true');p.add_argument('--wad-poll',action='store_true');p.add_argument('--dispatch-atomic',action='store_true');p.add_argument('--doom-dma',action='store_true');p.add_argument('--wad-ring',action='store_true');p.add_argument('--wad-profile',action='store_true');p.add_argument('--peer-yield',action='store_true');p.add_argument('--dma-proof',action='store_true');a=p.parse_args()
card_profile=a.card_profile or ('accele160' if a.profile=='accele160' else 'dac960pg')
require_workflow(card_profile,'rtems_accele160' if a.profile=='accele160' else 'rtems_legacy')
if a.wad_ring and not (a.doom_dma and a.wad_batch):p.error('WAD ring requires DMA and batch runtime')
if a.doom_dma and not (a.doom_engine and a.resident_upload and a.owned_mib==12 and a.dispatch_atomic):p.error('Doom DMA requires owned play engine and atomic dispatch')
if a.dma_proof and not (a.profile=='residentnet' and a.owned_mib==12 and a.dispatch_atomic and not a.resident_upload):p.error('DMA proof requires isolated owned 12 MiB without application upload')
if a.dispatch_atomic and a.profile!='residentnet':p.error('atomic dispatch requires residentnet proof profile')
if a.wad_batch and not (a.wad_poll and a.doom_runtime and a.doom_engine):p.error('WAD batches require polling, owned runtime and the protected engine profile')
if a.wad_poll and not a.doom_runtime:p.error('WAD polling requires the owned runtime profile')
startup_profile=bool(a.doom_engine and (a.doom_engine/'manifest.json').exists() and json.loads((a.doom_engine/'manifest.json').read_text()).get('startup'))
if startup_profile and not (a.wad_batch and a.dispatch_atomic and a.owned_mib==12):p.error('Doom startup requires validated batching, atomic dispatch and owned 12 MiB')
if a.doom_engine and not a.doom_runtime:p.error('engine admission requires owned runtime')
if a.doom_runtime and not a.doom_shared:p.error('runtime entry requires shared Doom arena')
if a.doom_shared and not a.doom_heap:p.error('shared arena requires Doom heap')
if a.doom_heap and not a.resident_upload:p.error("Doom heap requires resident upload")
if a.resident_upload and a.owned_mib not in (10,12):p.error("resident upload requires 10 or 12 MiB exclusive ownership")
if a.owned_mib and (not a.queue_reclaim or a.fault_test or a.heap_test):p.error("owned RAM requires release queue-reclaim profile")
if a.secondary_reset and a.profile!="residentnet":p.error("secondary reset requires residentnet")
if a.fault_owner and not a.secondary_reset:p.error("fault ownership requires secondary reset")
if a.fault_test and not a.fault_owner:p.error("fault test requires fault ownership")
if a.extra_ram and not a.fault_owner:p.error("extra RAM requires exclusive fault ownership")
if a.general_heap and not a.extra_ram:p.error("general heap requires validated extra RAM")
if a.heap_test>=5 and not a.queue_reclaim:p.error("fallback fault tests require queue reclaim")
if a.heap_test and not a.general_heap:p.error("heap fault test requires general heap")
if a.queue_reclaim and not a.heap_shared:p.error("queue reclaim requires shared heap instrumentation")
if a.heap_shared and not a.general_heap:p.error("shared heap requires general heap")
if a.heap_test and a.fault_test:p.error("select one fault injection per image")
here=Path(__file__).resolve().parent;work=a.work.resolve();src=work/'rtems-4.6.6';out=work/a.profile;out.mkdir(exist_ok=True,parents=True)
for row in json.loads((here/'sources.json').read_text())['sources']:
 if a.profile not in ('net','autonet','residentnet') and row['name'].startswith('lwip'):continue
 path=work/'sources'/row['name']
 if hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:raise SystemExit('source hash mismatch: '+str(path))
if not src.exists():subprocess.run(['tar','-xjf',str(work/'sources/rtems-4.6.6.tar.bz2'),'-C',str(work)],check=True)
newlib=work/'newlib-1.11.0'
if not newlib.exists():
 subprocess.run(['tar','-xzf',str(work/'sources/newlib-1.11.0.tar.gz'),'-C',str(work)],check=True)
 subprocess.run(['patch','-p1','-i',str(work/'sources/newlib-1.11.0-rtems-20030605.diff')],cwd=newlib,check=True)
inc=out/'include';inc.mkdir(exist_ok=True)
for rel in ['include','libcsupport/include','score/include','score/inline','rtems/include','rtems/inline','sapi/include','sapi/inline','score/cpu/i960']:
 d=src/'cpukit'/rel
 for f in d.rglob('*'):
  if f.suffix not in ('.h','.inl'):continue
  target=inc/f.relative_to(d);target.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(f,target)
(inc/'rtems/score/cpuopts.h').write_text('#define RTEMS_INLINE 1\n#define USE_INLINES 1\n#define RTEMS_CPU "i960"\n#define RTEMS_CPU_MODEL "rp"\n')
if a.profile in ('session','net','irq','auto','autonet','mu','muctl','irqctx','muctx','switch','defer','mustop','stopcases','contain','containcases','ownership','ownirq','persistirq','leaseirq','handoff','exclusive','residentnet'):
 shutil.copyfile(here/'transport/buffer_io.h',inc/'buffer_io.h')
# Newlib's patched machine/types already owns signed C99 integer typedefs.
f=inc/'rtems/stdint.h';s=f.read_text();start=s.index('typedef signed8');end=s.index('typedef unsigned8',start);f.write_text(s[:start]+'#include <machine/types.h>\n\n'+s[end:])
# The legacy generic header wrongly marks this little-endian build big-endian.
f=inc/'rtems/score/cpu.h';s=f.read_text().replace('#define CPU_BIG_ENDIAN                           TRUE','#define CPU_BIG_ENDIAN                           FALSE').replace('#define CPU_LITTLE_ENDIAN                        FALSE','#define CPU_LITTLE_ENDIAN                        TRUE')
# Bounded profile keeps firmware vector/interrupt-stack ownership, interrupts masked.
s=s.replace('#define CPU_HAS_HARDWARE_INTERRUPT_STACK TRUE','#define CPU_HAS_HARDWARE_INTERRUPT_STACK FALSE').replace('#define CPU_ALLOCATE_INTERRUPT_STACK     TRUE','#define CPU_ALLOCATE_INTERRUPT_STACK     FALSE')
s=s.replace('unsigned32 _level = (newlevel);','unsigned32 _level = 31u << 16; /* cooperative profile stays masked */')
s=s.replace('_base_pc | ((_isr) << 16)','_base_pc | (31u << 16)')
start=s.index('#define _CPU_Fatal_halt');end=s.index('/* end of Fatal Error Manager macros */',start)
s=s[:start]+'void bounded_fatal(unsigned int code);\n#define _CPU_Fatal_halt(code) bounded_fatal(code)\n\n'+s[end:];f.write_text(s)
profile_dir=here/('irq' if a.profile in ('auto','mu','muctl','irqctx','muctx') else 'net' if a.profile=='autonet' else 'switch' if a.profile in ('defer','mustop','stopcases','contain','containcases') else a.profile)
flags=['-DI960_TARGET','-mrp','-Os','-fno-builtin','-ffreestanding','-D__rtems__','-DUSE_INLINES','-I'+str(inc),'-I'+str(newlib/'newlib/libc/include')]
if a.profile in ('net','autonet','residentnet'):
 lwip=work/'lwip-STABLE-2_1_3_RELEASE'
 if not lwip.exists():subprocess.run(['tar','-xzf',str(work/'sources/lwip-2.1.3.tar.gz'),'-C',str(work)],check=True)
 patch_lwip(lwip)
 flags += ['-I'+str(here/'net'),'-I'+str(lwip/'src/include')]
if a.profile in ('auto','mu','muctl','muctx'):flags+=['-DI960_BACKGROUND']
if a.profile in ('irqctx','muctx'):flags+=['-DI960_OWNED_STACK']
if a.profile=='irqctx':flags+=['-DI960_CONTEXT_TEST']
if a.profile in ('muctl','muctx'):flags+=['-DI960_MU_FRAMED']
if a.profile=='mu':flags+=['-DI960_MU_ECHO']
if a.profile=='autonet':flags+=['-DI960_BACKGROUND_NET']
if a.profile=='defer':flags+=['-DI960_DEFER_TEST']
if a.profile in ('mustop','stopcases','contain','containcases'):flags+=['-DI960_STOP_TEST']
if a.profile in ('stopcases','containcases'):flags+=['-DI960_STOP_CASES']
if a.profile in ('contain','containcases'):flags+=['-DI960_CONTAIN_TEST']
if a.doom_dma:flags+=['-DI960_DOOM_DMA']
if a.wad_ring:flags+=['-DI960_WAD_RING']
if a.peer_yield:
 assert a.profile=='residentnet' and a.wad_profile and a.doom_engine and a.heap_shared and not a.fault_test and not a.heap_test
 flags+=['-DI960_PEER_YIELD']
if a.wad_profile:
 assert a.wad_ring and a.heap_shared
 flags+=['-DI960_WAD_PROFILE']
if a.dma_proof:flags+=['-DI960_DMA_PROOF']
if a.secondary_reset:flags+=['-DI960_SECONDARY_RESET']
if a.fault_owner:flags+=['-DI960_FAULT_OWNER','-DI960_FAULT_TEST='+str(a.fault_test)]
if a.resident_upload:flags+=['-DI960_RESIDENT_UPLOAD']
if a.doom_heap:flags+=['-DI960_DOOM_HEAP']
if a.doom_shared:flags+=['-DI960_DOOM_SHARED']
if a.doom_runtime:
 flags+=['-DI960_DOOM_RUNTIME','-DI960_DOOM_RELOCATE','-DI960_DOOM_CACHE','-DI960_DOOM_OWNED']
 subprocess.run(['python3',str(here.parent/'game/doom/runtime/entry/build.py'),'--out',str(out/'entry'),'--cross',a.cross],check=True)
 shutil.copyfile(out/'entry/runtime_probe_bytes.h',inc/'runtime_probe_bytes.h')
 subprocess.run(['python3',str(here.parent/'game/doom/runtime/relocate/build.py'),'--out',str(out/'entry/relocate'),'--cross',a.cross],check=True)
 shutil.copyfile(out/'entry/relocate/relocated_probe_bytes.h',inc/'relocated_probe_bytes.h')
 subprocess.run(['python3',str(here.parent/'game/doom/runtime/cache/build_probe.py'),'--out',str(out/'entry/cache'),'--cross',a.cross],check=True)
 shutil.copyfile(out/'entry/cache/cache_probe_bytes.h',inc/'cache_probe_bytes.h')
 subprocess.run(['python3',str(here.parent/'game/doom/runtime/owned/build.py'),'--out',str(out/'entry/owned'),'--cross',a.cross,'--newlib',str(newlib)],check=True)
 shutil.copyfile(out/'entry/owned/owned_probe_bytes.h',inc/'owned_probe_bytes.h')
if a.wad_batch:
 flags+=['-DI960_WAD_BATCH']
 (out/'entry/cache/batch-enabled').write_text('WAB1 4096\n')
if a.wad_poll:flags+=['-DI960_WAD_POLL']
if a.doom_engine:
 flags+=['-DI960_DOOM_ENGINE']
 if json.loads((a.doom_engine/'manifest.json').read_text()).get('pingpong'):flags+=['-DI960_PINGPONG']
 if json.loads((a.doom_engine/'manifest.json').read_text()).get('cpu_profile'):flags+=['-DI960_DOOM_CPU_PROFILE']
 if startup_profile:flags+=['-DI960_DOOM_STARTUP']
 if startup_profile and json.loads((a.doom_engine/'manifest.json').read_text())['startup'].get('play'):flags+=['-DI960_DOOM_PLAY']
 if startup_profile and any(json.loads((a.doom_engine/'manifest.json').read_text())['startup'].get(k) for k in ('checkpoints_sha256','checkpoint_api')):flags+=['-DI960_DOOM_CHECKPOINTS']
 if startup_profile and json.loads((a.doom_engine/'manifest.json').read_text())['startup'].get('checkpoint_barriers'):flags+=['-DI960_DOOM_CHECKPOINT_BARRIERS']
 shutil.copyfile(a.doom_engine/'engine_identity.h',inc/'engine_identity.h')
 engine_out=out/'entry/engine';engine_out.mkdir(parents=True,exist_ok=True)
 for name in ('manifest.json','template.bin','relocations.bin','engine_identity.h'):shutil.copyfile(a.doom_engine/name,engine_out/name)
 if (a.doom_engine/'visible-frames.bin').exists():shutil.copyfile(a.doom_engine/'visible-frames.bin',engine_out/'visible-frames.bin')
 if (a.doom_engine/'startup-checkpoints.bin').exists():shutil.copyfile(a.doom_engine/'startup-checkpoints.bin',engine_out/'startup-checkpoints.bin')
 if (a.doom_engine/'startup-requests.bin').exists():shutil.copyfile(a.doom_engine/'startup-requests.bin',engine_out/'startup-requests.bin')
if a.doom_dma and '-DI960_DOOM_PLAY' not in flags:p.error('Doom DMA requires a playable engine manifest')
if a.owned_mib:flags+=['-DI960_OWNED_MIB='+str(a.owned_mib)]
if a.extra_ram:flags+=['-DI960_EXTRA_RAM']
if a.heap_shared:flags+=['-DI960_HEAP_SHARED']
if a.queue_reclaim:flags+=['-DI960_QUEUE_RECLAIM']
if a.general_heap:flags+=['-DI960_GENERAL_HEAP','-DI960_HEAP_TEST='+str(a.heap_test)]
sources=[]
for folder in ['score/src','rtems/src','sapi/src']:
 sources += [f for f in sorted((src/'cpukit'/folder).glob('*.c')) if not f.stem.endswith('mp') and f.stem not in ('mpci','mppkt','mpproc','posixapi','itronapi')]
sources += [src/'cpukit/score/cpu/i960/cpu.c']
dispatch_patch=None
if a.dispatch_atomic:
 from dispatch_gap import generate
 original=src/'cpukit/score/src/threaddispatch.c';patched=out/'patches/threaddispatch.c'
 dispatch_patch=generate(original,patched);sources=[patched if f==original else f for f in sources]
 flags+=['-DI960_DISPATCH_ATOMIC']
objs=[]
for f in sources:
 obj=out/(('score' if f==out/'patches/threaddispatch.c' else f.parent.parent.name)+'_'+f.stem+'.o');objs.append(obj)
 r=subprocess.run([a.cross+'gcc',*flags,'-c',str(f),'-o',str(obj)],capture_output=True,text=True)
 if r.returncode:print(r.stderr);raise SystemExit(f'Compile failed: {f}')
subprocess.run([a.cross+'ar','rcs',str(out/'librtems-bounded.a'),*map(str,objs)],check=True)
if a.profile in ('net','autonet','residentnet'):
 netobjs=[]
 for f in sorted((lwip/'src/core').glob('*.c'))+sorted((lwip/'src/core/ipv4').glob('*.c'))+sorted((lwip/'src/core/ipv6').glob('*.c')):
  obj=out/('lwip_'+f.stem+'.o');netobjs.append(obj)
  subprocess.run([a.cross+'gcc',*flags,'-c',str(f),'-o',str(obj)],check=True)
 subprocess.run([a.cross+'ar','rcs',str(out/'liblwip.a'),*map(str,netobjs)],check=True)
for f in sorted(profile_dir.glob('*')):
 if f.suffix not in ('.c','.S') or f.name.startswith(('.', 'test_')):continue
 subprocess.run([a.cross+'gcc',*flags,'-c',str(f),'-o',str(out/(f.stem+'.o'))],check=True)
subprocess.run([a.cross+'ld','-T',str(profile_dir/('link-engine.ld' if a.doom_engine else 'link-upload.ld' if a.resident_upload else 'link.ld')),'-Map='+str(out/'kernel.map'),'-o',str(out/'kernel.elf'),*[str(out/(f.stem+'.o')) for f in sorted(profile_dir.glob('*')) if f.suffix in ('.c','.S') and not f.name.startswith(('.', 'test_'))],str(out/'librtems-bounded.a'),*([str(out/'liblwip.a')] if a.profile in ('net','autonet','residentnet') else [])],check=True)
subprocess.run([a.cross+'objcopy','-O','binary',str(out/'kernel.elf'),str(out/'kernel.bin')],check=True)
with (out/'kernel.dis').open('w') as f:subprocess.run([a.cross+'objdump','-dr',str(out/'kernel.elf')],stdout=f,check=True)
subprocess.run([a.cross.replace('coff-','elf-')+'size',str(out/'kernel.elf')],check=True)

with (out/'kernel.symbols').open('w') as f:subprocess.run([a.cross+'nm','-n',str(out/'kernel.elf')],stdout=f,check=True)

metadata=dict(dispatch_patch=dispatch_patch,card_profile=card_profile,profile=a.profile,compiler=subprocess.check_output([a.cross+'gcc','--version'],text=True).splitlines()[0],payload_bytes=(out/'kernel.bin').stat().st_size,payload_sha256=hashlib.sha256((out/'kernel.bin').read_bytes()).hexdigest(),flags=flags,sources=json.loads((here/'sources.json').read_text())['sources'])
(out/'build.json').write_text(json.dumps(metadata,indent=2)+'\n')
