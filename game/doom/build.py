#!/usr/bin/env python3
"""Pinned-source compile inventory; i960 output is relocatable, NOT loadable firmware."""
import argparse,hashlib,json,re,shutil,subprocess,tarfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--archive',type=Path,required=True);p.add_argument('--target',choices=['i960','host32','host64'],required=True);p.add_argument('--newlib',type=Path,default=Path('/home/mit/i960-rtems-web-20261011/scsi-drain/newlib-1.11.0'));p.add_argument('--arena-runtime',action='store_true');p.add_argument('--wad-cache',action='store_true');p.add_argument('--sanitize',action='store_true');p.add_argument('--startup',action='store_true');p.add_argument('--platform-runtime',action='store_true');a=p.parse_args()
assert not a.platform_runtime or (a.target in ('i960','host32') and a.wad_cache), 'private platform requires i960 WAD-cache build'
assert not a.wad_cache or a.arena_runtime, 'WAD cache requires the arena profile'
assert hashlib.sha256(a.archive.read_bytes()).hexdigest()=='26f8f60daa6c6e4d3c01e5eac9fb700d592dede803d13ac848154ff356b2a2e7', 'source hash mismatch'
here=Path(__file__).resolve().parent;work=a.work.resolve();work.mkdir(parents=True,exist_ok=True)
with tarfile.open(a.archive) as tf:tf.extractall(work,filter='data')
src=work/'doomgeneric-e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric'
# C99 loop declarations are supported by GNU99 even on GCC 3.3.
flags=['-std=gnu99','-Os','-fno-strict-aliasing','-fcommon','-DCMAP256','-DDOOMGENERIC_RESX=320','-DDOOMGENERIC_RESY=200','-I'+str(src)]
patches=[]
def patch(name,old,new):
 f=src/name;s=f.read_text();assert s.count(old)==1,(name,old);f.write_text(s.replace(old,new));patches.append(dict(file=name,before=old,after=new))
patch('doomgeneric.c','DOOMGENERIC_RESX * DOOMGENERIC_RESY * 4','DOOMGENERIC_RESX * DOOMGENERIC_RESY * sizeof(pixel_t)')
patch('i_video.c','I_VideoBuffer = (byte*)Z_Malloc (SCREENWIDTH * SCREENHEIGHT, PU_STATIC, NULL);','I_VideoBuffer = (byte*)Z_Malloc (SCREENWIDTH * SCREENHEIGHT, PU_STATIC, NULL);\n    memset(I_VideoBuffer, 0, SCREENWIDTH * SCREENHEIGHT); /* deterministic initial wipe */')
# Bounds belong to masked posts, not the wrapping wall-texture path.
shutil.copyfile(here/'bounded_column.h', src/'bounded_column.h')
patch('r_draw.c', '#include "r_local.h"', '#include "r_local.h"\n#include "bounded_column.h"\nint dc_postlength; /* zero outside masked post dispatch */')
for old,new,count in [
 ('dc_source[(frac>>FRACBITS)&127]', 'dc_source[R_ColumnIndex(frac, dc_postlength, 1)]', 2),
 ('dc_source[frac>>FRACBITS]', 'dc_source[R_ColumnIndex(frac, dc_postlength, 0)]', 3)]:
 f=src/'r_draw.c';s=f.read_text();assert s.count(old)==count
 f.write_text(s.replace(old,new));patches.append(dict(file='r_draw.c',before=old,after=new,count=count))
patch('r_things.c', '#include "r_local.h"', '#include "r_local.h"\nextern int dc_postlength;')
patch('r_things.c', 'if (dc_yl <= dc_yh)', 'if (dc_yl <= dc_yh && column->length > 0)')
patch('r_things.c', '    colfunc ();', '    dc_postlength = column->length;\n\t    colfunc ();\n\t    dc_postlength = 0;')
# The exact same instrument-free engine is used for target sizing.
objects=re.search(r'^SRC_DOOM = (.*)$',(src/'Makefile').read_text(),re.M)[1].split()
sources=[src/(s[:-2]+'.c') for s in objects if s!='doomgeneric_xlib.o']
out=work/a.target;out.mkdir(exist_ok=True)
if a.target=='i960':
 cc='/home/mit/i960/tools/bin/i960-coff-gcc';prefix='/home/mit/i960/tools/bin/i960-coff-'
 flags+=['-mrp','-ffreestanding','-fno-builtin','-I'+str(here/'include'),'-I'+str(a.newlib/'newlib/libc/include')]
elif a.platform_runtime:
 cc='gcc';prefix='';flags+=['-m32','-D__SINGLE_THREAD__','-funsigned-char','-ffreestanding','-fno-builtin','-I'+str(here/'include'),'-I'+str(a.newlib/'newlib/libc/include')]
else:
 cc='gcc';prefix='';flags+=['-m32' if a.target=='host32' else '-m64','-g','-fstack-usage','-DPROFILE_HOST']
 sources += [here/'profile.c']
 patch('z_zone.c','memzone_t*\tmainzone;','memzone_t*\tmainzone;\nvoid DG_ZoneSample(void);\nextern unsigned prof_zone_purges;')
 patch('z_zone.c','Z_Free ((byte *)rover+sizeof(memblock_t));','prof_zone_purges++;\n                Z_Free ((byte *)rover+sizeof(memblock_t));')
 if not a.wad_cache:patch('w_file_stdc.c','    return result;', '    extern void DG_WadRead(unsigned,unsigned);\n    DG_WadRead(buffer_len,result);\n    return result;')
 patch('z_zone.c','    return result;','    DG_ZoneSample();\n    return result;')
 with (src/'z_zone.c').open('a') as f:f.write((here/'zone_profile.inc').read_text())
runtime_sources=[]
if a.arena_runtime and not a.platform_runtime:
 runtime_sources=[here/'runtime/heap.c',here/'runtime/libc.c',here/'../../loader/segmented/arena.c']
 sources+=runtime_sources
 flags+=['-I'+str(here/'runtime')]
 if a.target!='i960': flags+=['-DPROFILE_ARENA']
if a.wad_cache:
 sources=[f for f in sources if f.name!='w_file_stdc.c']+[here/'runtime/cache/cache.c',here/'runtime/cache/backend.c']
 flags+=['-DDOOM_WAD_CACHE','-I'+str(here/'runtime/cache')]
if a.startup:
 assert a.platform_runtime
 flags+=['-DDOOM_STARTUP']
 if a.target=='i960':flags+=['-mold-align'] # private Doom zone promises pointer (4-byte) alignment
if a.sanitize:
 assert a.platform_runtime and a.target=='host32'
 flags+=['-fsanitize=address','-g','-fno-omit-frame-pointer']
commands=[];failures=[];objs=[]
with (out/'compile.log').open('w') as log:
 for f in sources:
  obj=out/(f.stem+'.o');renames=(['-D'+n+'=doom_'+n for n in ('malloc','calloc','realloc','free','strdup')] if a.arena_runtime and not a.platform_runtime and a.target=='i960' and f not in runtime_sources else []);cmd=[cc,*flags,*renames,*(['-finstrument-functions'] if a.target!='i960' and not a.platform_runtime and f.name!='profile.c' and not (a.arena_runtime and f in runtime_sources) else []),'-c',str(f),'-o',str(obj)];commands.append(cmd)
  r=subprocess.run(cmd,stdout=log,stderr=log)
  if r.returncode:failures.append(f.name)
  else:objs.append(str(obj))
(out/'build.json').write_text(json.dumps(dict(target=a.target,compiler=subprocess.check_output([cc,'--version'],text=True).splitlines()[0],flags=flags,source_count=len(sources),failures=failures,commands=commands,patches=patches),indent=2)+'\n')
if failures:raise SystemExit('Compile failed: '+str(failures))
if a.platform_runtime and a.target=='host32':
 subprocess.run(['ld','-m','elf_i386','-r','-d','-o',str(out/'doom-engine.o'),*objs],check=True)
elif a.target=='i960':
 subprocess.run([prefix+'ld','-r','-d','-o',str(out/'doom-engine.o'),*objs],check=True)
 for tool,args,name in [('nm',['-u'],'undefined.txt'),('size',['-A'],'sections.txt'),('nm',['-S','--size-sort'],'symbols.txt'),('objdump',['-h'],'headers.txt')]:
  with (out/name).open('w') as f:subprocess.run([('/home/mit/i960/tools/bin/i960-elf-size' if tool=='size' else prefix+tool),*args,str(out/'doom-engine.o')],stdout=f,check=True)
else:
 cmd=[cc,*objs,'-m32' if a.target=='host32' else '-m64','-Wl,--wrap=malloc,--wrap=calloc,--wrap=realloc,--wrap=free,--wrap=strdup','-Wl,-Map='+str(out/'doom.map'),'-lm','-o',str(out/'doom-profile')]
 with (out/'link.log').open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=f)
 if r.returncode:raise SystemExit('host link failed')
print(out)
