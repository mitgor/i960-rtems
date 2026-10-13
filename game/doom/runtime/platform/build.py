#!/usr/bin/env python3
"""Build private pinned Newlib, rename every libc/port symbol, final-link oracle."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--newlib',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--engine',type=Path);p.add_argument('--doom',type=Path,required=True);p.add_argument('--target',choices=('i960','host32'),default='i960');p.add_argument('--startup',action='store_true');p.add_argument('--sanitize',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
r=Path(__file__).resolve().parent;lib=a.newlib/'newlib/libc';cross='/home/mit/i960/tools/bin/i960-coff-' if a.target=='i960' else '';cc=cross+'gcc' if cross else 'gcc'
flags=['-Os','-fno-builtin','-ffreestanding','-D__SINGLE_THREAD__','-DWANT_PRINTF_LONG_LONG','-DCMAP256','-I'+str(lib/'include'),'-I'+str(a.newlib/'newlib/libm/common'),'-I'+str(r.parents[1]/'include'),'-I'+str(a.doom),'-I'+str(r)]+(['-mrp','-msoft-float'] if cross else ['-m32','-D__i386__','-funsigned-char','-D_I386MACH_ALLOW_HW_INTERRUPTS'])
if a.startup and cross:flags+=['-mold-align'] # same private ABI as the admitted engine
if a.sanitize:
 assert a.target=='host32'
 flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-g']
sources=[]
for folder in ('string','ctype'):sources+=[f for f in sorted((lib/folder).glob('*.c')) if f.name not in ('strdup.c','strdup_r.c')]
stdio=(lib/'stdio/Makefile.am').read_text().split('GENERAL_SOURCES =',1)[1].split('## The following',1)[0]
sources += [lib/'stdio'/name for name in re.findall(r'\b\w+\.c\b',stdio)]+[lib/'stdio/vfprintf.c']
for group,names in {'stdlib':'abs atoi atol atof strtod strtol strtoul dtoa mprec mbtowc mbtowc_r wctomb wctomb_r mblen mblen_r mbstowcs mbstowcs_r wcstombs wcstombs_r strtoll_r strtoull_r', 'locale':'locale', 'reent':'impure reent closer openr readr writer lseekr fstatr unlinkr linkr', 'errno':'errno'}.items():sources += [lib/group/(n+'.c') for n in names.split()]
sources += [a.newlib/'newlib/libm/math'/n for n in ('s_isinf.c','s_isnan.c','s_infconst.c')]
sources += [r/'port.c',r/'../cache/cache.c']
if a.engine:sources += [r/('startup_entry.c' if a.startup else 'engine_entry.c')]
sources += [lib/('machine/i960/setjmp.S' if cross else 'machine/i386/setjmp.S')]
objs=[];commands=[];source_hashes={};patches=[]
with (a.out/'compile.log').open('w') as log:
 for i,source in enumerate(sources):
  original=source;source_hashes[str(source)]=hashlib.sha256(source.read_bytes()).hexdigest()
  if source.name=='vfprintf.c':
   text=source.read_text();old='GET_ARG(N, ap, quad_ptr_t *)';assert text.count(old)==1
   source=a.out/'patched-vfprintf.c';source.write_text(text.replace(old,'GET_ARG(N, ap, quad_ptr_t)'));patches.append(dict(source=str(original),before=old,after='GET_ARG(N, ap, quad_ptr_t)',sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
  obj=a.out/(str(i)+'-'+source.stem+'.o');cmd=[cc,*flags,'-I'+str(original.parent),'-c',str(source),'-o',str(obj)];commands.append(cmd)
  run=subprocess.run(cmd,stdout=log,stderr=log)
  if run.returncode:raise SystemExit('compile failed: '+str(source))
  objs.append(obj)
# Archive selection keeps unused functions out of the engine image.
archive=a.out/'raw-newlib.a';subprocess.run([cross+'ar' if cross else 'ar','rcs',str(archive),*map(str,objs)],check=True)
nm=cross+'nm' if cross else 'nm';objcopy=cross+'objcopy' if cross else 'objcopy'
raw=subprocess.check_output([nm,'--defined-only',str(archive)],text=True)
defined=set(row.split()[-1] for row in raw.splitlines() if len(row.split())>=3 and row.split()[-2].upper() in 'TDBRSCVW')
# Preserve application API and cache names; namespace all other definitions,
# including Newlib reentrancy, ctype, errno, syscall and allocation state.
preserve=lambda s:s.lstrip('_').startswith(('doom_platform_','doom_cache_','doom_engine_'))
mapping={s:('_doom_nl'+s if cross else 'doom_nl_'+s) for s in defined if not preserve(s)}
(a.out/'rename.txt').write_text(''.join(k+' '+v+'\n' for k,v in sorted(mapping.items())))
private=a.out/'private-newlib.a';subprocess.run([objcopy,'--redefine-syms='+str(a.out/'rename.txt'),str(archive),str(private)],check=True)
report=dict(target=a.target,sanitized=a.sanitize,patches=patches,sources=source_hashes,commands=commands,renamed_symbols=mapping,archive_sha256=hashlib.sha256(private.read_bytes()).hexdigest())
if a.engine:
 engine=a.out/'engine-private.o';subprocess.run([objcopy,'--redefine-syms='+str(a.out/'rename.txt'),str(a.engine),str(engine)],check=True)
 libgcc=Path(subprocess.check_output([cc,*(['-mrp','-msoft-float'] if cross else ['-m32']),'-print-libgcc-file-name'],text=True).strip())
 private_gcc=a.out/'private-libgcc.a';subprocess.run([objcopy,'--redefine-syms='+str(a.out/'rename.txt'),str(libgcc),str(private_gcc)],check=True)
 image=a.out/'doom-platform.o';cmd=[cross+'ld',*(['-m','elf_i386'] if not cross else []),'-u','_doom_engine_entry' if cross else 'doom_engine_entry','-r','-d','-o',str(image),str(engine),str(private),str(private_gcc)]
 subprocess.run(cmd,check=True)
 undefined=subprocess.check_output([nm,'-u',str(image)],text=True);(a.out/'undefined.txt').write_text(undefined)
 report.update(undefined=sorted(row.split()[-1] for row in undefined.splitlines()),libgcc_sha256=hashlib.sha256(libgcc.read_bytes()).hexdigest(),image_sha256=hashlib.sha256(image.read_bytes()).hexdigest())
 with (a.out/'sections.txt').open('w') as f:subprocess.run([str(Path(cross).parent/'i960-elf-size') if cross else 'size','-A',str(image)],stdout=f,check=True)
 if not undefined.strip():
  final=a.out/'doom-platform.elf';subprocess.run([cross+'ld',*(['-m','elf_i386'] if not cross else []),'-e','_doom_engine_entry' if cross else 'doom_engine_entry','-o',str(final),str(image)],check=True);report['final_link_passed']=True
 else:report['final_link_passed']=False
(a.out/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('commands','sources','renamed_symbols')},indent=2))
