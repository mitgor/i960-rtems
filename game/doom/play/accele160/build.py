#!/usr/bin/env python3
"""Reproduce the persistent new-card engine/kernel without touching hardware."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

p=argparse.ArgumentParser(description=__doc__)
for name in ('work','archive','newlib','rtems-build'):
    p.add_argument('--'+name,type=Path,required=True)
p.add_argument('--cross',default='/home/mit/i960/tools/bin/i960-coff-')
a=p.parse_args();root=Path(__file__).resolve().parents[4];w=a.work.resolve()
if w.exists():p.error('choose a new build directory')
w.mkdir(parents=True);project=w/'project'
for name in ('game','rtems','host','loader','card_profiles'):
    shutil.copytree(root/name,project/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.o'))

def run(args,name,env=None):
    print(name,flush=True)
    with (w/(name+'.log')).open('w') as log:
        subprocess.run(list(map(str,args)),stdout=log,stderr=subprocess.STDOUT,env=env,check=True)

for suffix,target in (('host','host32'),('cross','i960')):
    run([sys.executable,project/'game/doom/build.py','--work',w/('engine-'+suffix),
         '--archive',a.archive,'--target',target,'--card-profile','accele160','--cross',a.cross,
         '--newlib',a.newlib,'--arena-runtime','--wad-cache','--wad-profile','--platform-runtime',
         '--startup','--checkpoints','--point-side-o0','--visible','--play',
         '--fast-render','--fast-columns','--wide-screen-copy'], 'engine-'+suffix)
    engine=w/('engine-'+suffix)
    doom=engine/'doomgeneric-e257a09527062bfb986b6e5e0780839b6cbd5b71/doomgeneric'
    run([sys.executable,project/'game/doom/runtime/platform/build.py','--newlib',a.newlib,
         '--out',w/('platform-'+suffix),'--doom',doom,'--engine',engine/target/'doom-engine.o',
         '--target',target,'--cross',a.cross,'--startup','--checkpoints','--visible','--play',
         '--persistent-play','--double-buffer','--frame-profile','--cpu-profile','--wad-profile',
         '--no-fnv','--direct-frame','--low-detail'], 'platform-'+suffix)
run([sys.executable,project/'game/doom/runtime/platform/pack_engine.py',
     '--build',w/'platform-cross','--out',w/'packed','--cross',a.cross],'pack')
run([sys.executable,project/'game/doom/runtime/engine/admit.py',w/'packed',
     '--build',w/'platform-cross','--out',w/'admission','--play','--pingpong','--cross',a.cross],'admit')
src=project/'rtems/accele160/doom_dma'
shutil.copyfile(w/'admission/engine_identity.h',src/'engine_identity.h')
import os
env=dict(os.environ,DOOM_PERSISTENT='1',DOOM_FPS_FRAMES='32',CARD_PROFILE='accele160')
run(['bash',src/'build.sh',a.rtems_build,Path(a.cross).parent,w/'kernel'],'kernel',env)
(w/'persistent-build.json').write_text(json.dumps(dict(card_profile='accele160',
    kernel_persistent=True,private_cache_map=True,low_detail=True,card_fnv=False,
    archive=str(a.archive),newlib=str(a.newlib),rtems_build=str(a.rtems_build)),indent=2)+'\n')
print('Persistent engine and kernel built:',w)
