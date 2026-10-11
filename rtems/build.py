#!/usr/bin/env python3
"""Build RTEMS 4.6.6 Classic core for a bounded DAC960 callback experiment."""
from pathlib import Path
import argparse,subprocess,shutil,json,hashlib
from lwip_patches import apply as patch_lwip
p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--profile',choices=['bounded','session','net','irq','auto','autonet','mu'],default='bounded');p.add_argument('--cross',default='/home/mit/i960/tools/bin/i960-coff-');a=p.parse_args()
here=Path(__file__).resolve().parent;work=a.work.resolve();src=work/'rtems-4.6.6';out=work/a.profile;out.mkdir(exist_ok=True,parents=True)
for row in json.loads((here/'sources.json').read_text())['sources']:
 if a.profile not in ('net','autonet') and row['name'].startswith('lwip'):continue
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
if a.profile in ('session','net','irq','auto','autonet','mu'):
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
profile_dir=here/('irq' if a.profile in ('auto','mu') else 'net' if a.profile=='autonet' else a.profile)
flags=['-DI960_TARGET','-mrp','-Os','-fno-builtin','-ffreestanding','-D__rtems__','-DUSE_INLINES','-I'+str(inc),'-I'+str(newlib/'newlib/libc/include')]
if a.profile in ('net','autonet'):
 lwip=work/'lwip-STABLE-2_1_3_RELEASE'
 if not lwip.exists():subprocess.run(['tar','-xzf',str(work/'sources/lwip-2.1.3.tar.gz'),'-C',str(work)],check=True)
 patch_lwip(lwip)
 flags += ['-I'+str(here/'net'),'-I'+str(lwip/'src/include')]
if a.profile in ('auto','mu'):flags+=['-DI960_BACKGROUND']
if a.profile=='mu':flags+=['-DI960_MU_ECHO']
if a.profile=='autonet':flags+=['-DI960_BACKGROUND_NET']
sources=[]
for folder in ['score/src','rtems/src','sapi/src']:
 sources += [f for f in sorted((src/'cpukit'/folder).glob('*.c')) if not f.stem.endswith('mp') and f.stem not in ('mpci','mppkt','mpproc','posixapi','itronapi')]
sources += [src/'cpukit/score/cpu/i960/cpu.c']
objs=[]
for f in sources:
 obj=out/(f.parent.parent.name+'_'+f.stem+'.o');objs.append(obj)
 r=subprocess.run([a.cross+'gcc',*flags,'-c',str(f),'-o',str(obj)],capture_output=True,text=True)
 if r.returncode:print(r.stderr);raise SystemExit(f'Compile failed: {f}')
subprocess.run([a.cross+'ar','rcs',str(out/'librtems-bounded.a'),*map(str,objs)],check=True)
if a.profile in ('net','autonet'):
 netobjs=[]
 for f in sorted((lwip/'src/core').glob('*.c'))+sorted((lwip/'src/core/ipv4').glob('*.c'))+sorted((lwip/'src/core/ipv6').glob('*.c')):
  obj=out/('lwip_'+f.stem+'.o');netobjs.append(obj)
  subprocess.run([a.cross+'gcc',*flags,'-c',str(f),'-o',str(obj)],check=True)
 subprocess.run([a.cross+'ar','rcs',str(out/'liblwip.a'),*map(str,netobjs)],check=True)
for f in sorted(profile_dir.glob('*')):
 if f.suffix not in ('.c','.S') or f.name.startswith(('.', 'test_')):continue
 subprocess.run([a.cross+'gcc',*flags,'-c',str(f),'-o',str(out/(f.stem+'.o'))],check=True)
subprocess.run([a.cross+'ld','-T',str(profile_dir/'link.ld'),'-Map='+str(out/'kernel.map'),'-o',str(out/'kernel.elf'),*[str(out/(f.stem+'.o')) for f in sorted(profile_dir.glob('*')) if f.suffix in ('.c','.S') and not f.name.startswith(('.', 'test_'))],str(out/'librtems-bounded.a'),*([str(out/'liblwip.a')] if a.profile in ('net','autonet') else [])],check=True)
subprocess.run([a.cross+'objcopy','-O','binary',str(out/'kernel.elf'),str(out/'kernel.bin')],check=True)
with (out/'kernel.dis').open('w') as f:subprocess.run([a.cross+'objdump','-dr',str(out/'kernel.elf')],stdout=f,check=True)
subprocess.run([a.cross.replace('coff-','elf-')+'size',str(out/'kernel.elf')],check=True)

with (out/'kernel.symbols').open('w') as f:subprocess.run([a.cross+'nm','-n',str(out/'kernel.elf')],stdout=f,check=True)

metadata=dict(profile=a.profile,compiler=subprocess.check_output([a.cross+'gcc','--version'],text=True).splitlines()[0],payload_bytes=(out/'kernel.bin').stat().st_size,payload_sha256=hashlib.sha256((out/'kernel.bin').read_bytes()).hexdigest(),flags=flags,sources=json.loads((here/'sources.json').read_text())['sources'])
(out/'build.json').write_text(json.dumps(metadata,indent=2)+'\n')
