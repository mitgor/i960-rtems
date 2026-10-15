#!/usr/bin/env python3
"""Build a tiny admitted producer; never accesses hardware."""
import argparse,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--cross',default='/home/mit/i960/tools/bin/i960-coff-');p.add_argument('--pingpong',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
r=Path(__file__).resolve().parents[3];obj=a.out/'doom-platform.o'
subprocess.run([a.cross+'gcc','-mrp','-Os',*(['-DPP_PRODUCER'] if a.pingpong else []),'-ffreestanding','-fno-builtin','-c',str(Path(__file__).with_name('engine.c')),'-o',str(a.out/'producer.o')],check=True)
subprocess.run([a.cross+'ld','-r','-d','-o',str(obj),str(a.out/'producer.o')],check=True)
(a.out/'build.json').write_text(json.dumps(dict(play=True,dma_stress=1,pingpong=a.pingpong,double_buffer=a.pingpong))+'\n')
subprocess.run(['python3',str(r/'game/doom/runtime/platform/pack_engine.py'),'--build',str(a.out),'--out',str(a.out/'packed'),'--cross',a.cross],check=True)
subprocess.run(['python3',str(r/'game/doom/runtime/engine/admit.py'),str(a.out/'packed'),'--build',str(a.out),'--out',str(a.out/'admission'),'--play','--dma-stress','--cross',a.cross],check=True)
