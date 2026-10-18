#!/usr/bin/env python3
"""Pinned-source compile inventory; i960 output is relocatable, NOT loadable firmware."""
import argparse,hashlib,json,re,shutil,subprocess,tarfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from card_profiles import require_workflow
p=argparse.ArgumentParser();p.add_argument('--cross',default='/home/mit/i960/tools/bin/i960-coff-');p.add_argument('--work',type=Path,required=True);p.add_argument('--archive',type=Path,required=True);p.add_argument('--target',choices=['i960','host32','host64'],required=True);p.add_argument('--card-profile',default=None);p.add_argument('--newlib',type=Path,default=Path('/home/mit/i960-rtems-web-20261011/scsi-drain/newlib-1.11.0'));p.add_argument('--arena-runtime',action='store_true');p.add_argument('--wad-cache',action='store_true');p.add_argument('--wad-profile',action='store_true');p.add_argument('--sanitize',action='store_true');p.add_argument('--startup',action='store_true');p.add_argument('--visible',action='store_true');p.add_argument('--play',action='store_true');p.add_argument('--checkpoints',action='store_true');p.add_argument('--point-side-o0',action='store_true');p.add_argument('--fast-point-side',action='store_true');p.add_argument('--platform-runtime',action='store_true');p.add_argument('--column-test',action='store_true');p.add_argument('--fast-render',action='store_true');p.add_argument('--fast-columns',action='store_true');p.add_argument('--span-four',action='store_true');p.add_argument('--runtime-flat',action='store_true');p.add_argument('--runtime-half-height',action='store_true');p.add_argument('--fast-walls',action='store_true');p.add_argument('--wall-profile',action='store_true');p.add_argument('--wall-profile-accele160',action='store_true');p.add_argument('--fast-clip-copy',action='store_true');p.add_argument('--wide-screen-copy',action='store_true');p.add_argument('--fixed-div-profile',action='store_true');div=p.add_mutually_exclusive_group();div.add_argument('--fast-fixed-div',dest='fast_fixed_div',action='store_true');div.add_argument('--no-fast-fixed-div',dest='fast_fixed_div',action='store_false');p.set_defaults(fast_fixed_div=None);p.add_argument('--input-trace',action='store_true');a=p.parse_args()
card_profile=a.card_profile or ('accele160' if a.wall_profile_accele160 else 'dac960pg')
require_workflow(card_profile,'doom_i960')
if a.wall_profile_accele160 and card_profile!='accele160':p.error('legacy AcceleRAID flag conflicts with card profile')
a.wall_profile_accele160=bool(a.wall_profile and card_profile=='accele160')
if a.fast_fixed_div is None:a.fast_fixed_div=bool(a.platform_runtime and a.play)
assert not a.platform_runtime or (a.target in ('i960','host32') and a.wad_cache), 'private platform requires i960 WAD-cache build'
assert not a.wad_cache or a.arena_runtime, 'WAD cache requires the arena profile'
assert not a.wide_screen_copy or (a.platform_runtime and a.play), 'wide copy requires private playable platform'
assert hashlib.sha256(a.archive.read_bytes()).hexdigest()=='26f8f60daa6c6e4d3c01e5eac9fb700d592dede803d13ac848154ff356b2a2e7', 'source hash mismatch'
here=Path(__file__).resolve().parent;work=a.work.resolve();work.mkdir(parents=True,exist_ok=True)
with tarfile.open(a.archive) as tf:tf.extractall(work,filter='data')
src=work/'doomgeneric-e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric'
# C99 loop declarations are supported by GNU99 even on GCC 3.3.
flags=['-std=gnu99','-Os','-fno-strict-aliasing','-fcommon','-DCMAP256','-DDOOMGENERIC_RESX=320','-DDOOMGENERIC_RESY=200','-I'+str(src)]
if a.wad_profile:
 assert a.wad_cache and a.platform_runtime
 flags+=['-DDOOM_WAD_PROFILE']
patches=[]
def patch(name,old,new,count=1):
 f=src/name;s=f.read_text();assert s.count(old)==count,(name,old);f.write_text(s.replace(old,new));patches.append(dict(file=name,before=old,after=new))
patch('doomgeneric.c','DOOMGENERIC_RESX * DOOMGENERIC_RESY * 4','DOOMGENERIC_RESX * DOOMGENERIC_RESY * sizeof(pixel_t)')
patch('i_video.c','I_VideoBuffer = (byte*)Z_Malloc (SCREENWIDTH * SCREENHEIGHT, PU_STATIC, NULL);','I_VideoBuffer = (byte*)Z_Malloc (SCREENWIDTH * SCREENHEIGHT, PU_STATIC, NULL);\n    memset(I_VideoBuffer, 0, SCREENWIDTH * SCREENHEIGHT); /* deterministic initial wipe */')
# Only the private platform uses the fixed indexed presentation fast path.
# Keep I_VideoBuffer persistent: renderer/HUD state must not follow a DMA slot.
if a.platform_runtime:
 shutil.copyfile(here/'screen_copy'/('wide.h' if a.wide_screen_copy else 'copy.h'),src/'screen_copy.h')
 patch('i_video.c','#include "doomgeneric.h"','#include "doomgeneric.h"\n#include "screen_copy.h"')
 patch('i_video.c','    while (y--)','    if (fb_scaling == 1 && s_Fb.xres == SCREENWIDTH && s_Fb.yres == SCREENHEIGHT && s_Fb.bits_per_pixel == 8) {\n        doom_screen_copy(line_out, line_in);\n    } else while (y--)')
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
if a.checkpoints:
 assert a.startup
 import sys
 sys.path.insert(0,str(here/'runtime/startup'))
 from instrument import apply
 shutil.copyfile(here/'runtime/startup/checkpoints.h',src/'checkpoints.h')
 apply(patch)
if a.play:assert a.visible
if a.visible:
 assert a.startup and a.checkpoints and (a.point_side_o0 or a.fast_point_side)
 # Keep game rendering; omit only the opening cosmetic wipe in this bounded proof.
 patch('d_main.c','if (gamestate != wipegamestate)', 'if (0) /* omit cosmetic transition for bounded visible-frame proof */')
 flags+=['-DDOOM_VISIBLE']
assert not (a.point_side_o0 and a.fast_point_side), "select one point-side implementation"
if a.point_side_o0 or a.fast_point_side:
 assert a.startup, 'comparison workaround is restricted to startup experiments'
 text=(src/'r_main.c').read_text();begin=text.index('int\nR_PointOnSide\n');end=text.index('\n\nint\nR_PointOnSegSide\n',begin)
 body=text[begin:end]
 # Preserve the original GPL header and actual Doom types in the split unit.
 (src/'r_point_side.c').write_text(text[:text.index('#include')]+'\n#include \"r_local.h\"\n'+body+'\n')
 if a.fast_point_side:shutil.copyfile(here/'point_side/point.c',src/'r_point_side.c')
 patch('r_main.c',body,'/* R_PointOnSide is compiled separately; see build.json. */')
if a.column_test:
 assert a.play and a.platform_runtime
 import sys
 sys.path.insert(0,str(here/'columns'))
 from patch import apply as apply_columns
 for name in ('column.h','column.c','column.S','selftest.c','vectors.h'):
  shutil.copyfile(here/'columns'/name,src/name)
 apply_columns(src,patch)
if a.fast_columns:
 assert a.platform_runtime and a.play and not a.column_test
 for name in ('column.h','column.c'):
  shutil.copyfile(here/'columns'/name,src/name)
 import importlib.util
 spec=importlib.util.spec_from_file_location('fixed_columns_patch',here/'columns/patch.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 module.apply(src,patch,fixed=True)
if a.fast_clip_copy:
 assert a.platform_runtime and a.play
 shutil.copyfile(here/'clip_copy/copy.h',src/'clip_copy.h')
 patch('r_segs.c','#include "r_local.h"','#include "r_local.h"\n#include "clip_copy.h"')
 for source in ('ceilingclip','floorclip'):
  old=f'memcpy (lastopening, {source}+start, 2*(rw_stopx-start));'
  new=f'doom_clip_copy (lastopening, {source}+start, (unsigned)(rw_stopx-start));'
  patch('r_segs.c',old,new)
if a.span_four:assert a.fast_render, "--span-four requires --fast-render"
if a.fast_render:
 assert a.platform_runtime and a.play and not a.column_test
 import importlib.util
 spec=importlib.util.spec_from_file_location('span_patch',here/'render/patch.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 apply_render=module.apply
 shutil.copyfile(here/'render/span.h',src/'span.h')
 if a.span_four:(src/'span.h').write_text('#define DOOM_SPAN_FOUR 1\n'+(src/'span.h').read_text())
 apply_render(src,patch)
if a.runtime_half_height:
 assert a.platform_runtime and a.play
 import importlib.util
 spec=importlib.util.spec_from_file_location('half_patch',here/'half_height/patch.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 shutil.copyfile(here/'half_height/half_height.h',src/'half_height.h')
 module.apply(patch)
if a.runtime_flat:
 assert a.platform_runtime and a.play
 import importlib.util
 spec=importlib.util.spec_from_file_location('flat_patch',here/'flat_planes/patch.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 shutil.copyfile(here/'flat_planes/fill.h',src/'flat_fill.h')
 module.apply(patch)
if a.fast_walls:assert a.platform_runtime and a.play
if a.wall_profile:
 assert a.platform_runtime and a.play and not (a.input_trace or a.fixed_div_profile)
 if a.wall_profile_accele160:flags+=['-DDOOM_WALL_PROFILE_ACCELE160']
 import importlib.util
 spec=importlib.util.spec_from_file_location('wall_patch',here/'wall_profile/patch.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 module.apply(src,patch)
assert not a.wall_profile_accele160 or a.wall_profile
if a.input_trace:
 patch('d_loop.c','static int maketic;','static int maketic;\nint doom_input_maketic(void){return maketic;}')
 assert a.platform_runtime and a.play and not a.fixed_div_profile
 patch('d_main.c','#include "doomstat.h"','#include "doomstat.h"\nextern void doom_input_event(unsigned,unsigned,unsigned);')
 patch('d_main.c','\tif (M_Responder (ev))\n\t    continue;', '\tint eaten;\n\tif(ev->type==ev_keydown||ev->type==ev_keyup)doom_input_event(2,ev->type==ev_keydown,ev->data1);\n\teaten=M_Responder(ev);\n\tif(ev->type==ev_keydown||ev->type==ev_keyup)doom_input_event(3,ev->type==ev_keydown,ev->data1);\n\tif(eaten)\n\t    continue;')
if a.fixed_div_profile or a.fast_fixed_div:
 assert a.platform_runtime and a.play
 import importlib.util
 spec=importlib.util.spec_from_file_location('fixed_div_patch',here/'fixed_div/patch.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 module.apply(src,patch,a.fast_fixed_div,a.fixed_div_profile)
 if a.fixed_div_profile:flags+=['-DDOOM_FIXED_DIV_PROFILE']
 if a.fast_fixed_div:flags+=['-DDOOM_FAST_FIXED_DIV']
# Explicit source list keeps optional profiler objects out unless selected.
objects=re.search(r'^SRC_DOOM = (.*)$',(src/'Makefile').read_text(),re.M)[1].split()
sources=[src/(s[:-2]+'.c') for s in objects if s!='doomgeneric_xlib.o']
if a.column_test:sources += [src/'column.c',src/'selftest.c'] + ([src/'column.S'] if a.target=='i960' else [])
if a.fixed_div_profile or a.fast_fixed_div:sources += [src/'fixed_divide.c'] + ([src/'fixed_divide.S'] if a.target=='i960' else [])
if a.fixed_div_profile:sources.append(src/'fixed_profile.c')
if a.fast_columns:sources.append(src/'column.c')
if a.wall_profile:sources.append(src/'wall_profile.c')
if a.point_side_o0 or a.fast_point_side:sources.append(src/'r_point_side.c')
out=work/a.target;out.mkdir(exist_ok=True)
if a.target=='i960':
 cc=a.cross+'gcc';prefix=a.cross
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
  obj=out/('column-asm.o' if f.name=='column.S' else 'fixed-divide-asm.o' if f.name=='fixed_divide.S' else f.stem+'.o');renames=(['-D'+n+'=doom_'+n for n in ('malloc','calloc','realloc','free','strdup')] if a.arena_runtime and not a.platform_runtime and a.target=='i960' and f not in runtime_sources else []);cmd=[cc,*flags,*(['-O2'] if (a.fast_render and f.name in ('r_bsp.c','r_plane.c','r_draw.c','column.c')) or (a.fast_walls and f.name=='r_segs.c') else []),*(['-O0'] if a.point_side_o0 and f.name=='r_point_side.c' else []),*renames,*(['-finstrument-functions'] if a.target!='i960' and not a.platform_runtime and f.name!='profile.c' and not (a.arena_runtime and f in runtime_sources) else []),'-c',str(f),'-o',str(obj)];commands.append(cmd)
  r=subprocess.run(cmd,stdout=log,stderr=log)
  if r.returncode:failures.append(f.name)
  else:objs.append(str(obj))
(out/'build.json').write_text(json.dumps(dict(card_profile=card_profile,runtime_half_height=a.runtime_half_height,runtime_flat=a.runtime_flat,span_four=a.span_four,wall_profile=a.wall_profile,wall_profile_accele160=a.wall_profile_accele160,fast_walls=a.fast_walls,fast_clip_copy=a.fast_clip_copy,wide_screen_copy=a.wide_screen_copy,fast_point_side=a.fast_point_side,input_trace=a.input_trace,fixed_div_profile=a.fixed_div_profile,fast_fixed_div=a.fast_fixed_div,fast_columns=a.fast_columns,fast_render=a.fast_render,screen_copy_sha256=hashlib.sha256((here/'screen_copy'/('wide.h' if a.wide_screen_copy else 'copy.h')).read_bytes()).hexdigest() if a.platform_runtime else None,clip_copy_sha256=hashlib.sha256((here/'clip_copy/copy.h').read_bytes()).hexdigest() if a.fast_clip_copy else None,wad_profile=a.wad_profile,column_test=a.column_test,point_side_o0=a.point_side_o0,target=a.target,compiler=subprocess.check_output([cc,'--version'],text=True).splitlines()[0],flags=flags,source_count=len(sources),failures=failures,commands=commands,patches=patches),indent=2)+'\n')
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
