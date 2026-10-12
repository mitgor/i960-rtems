#!/usr/bin/env python3
"""Build bounded BIO self-test with real segmented executable bytes."""
from pathlib import Path
import argparse, subprocess, hashlib,json
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--cross',default='/home/mit/i960/tools/bin/i960-coff-');a=p.parse_args()
r=Path(__file__).resolve().parent;o=a.out.resolve();o.mkdir(parents=True,exist_ok=True)
files=[r.parent/'runtime/buffer_start.s',r/'card_test.c',r/'arena.c',r/'image.c',r/'card_code.s'];objects=[]
for f in files:
 obj=o/(f.stem+'.o');objects.append(str(obj));subprocess.run([a.cross+'gcc','-mrp','-Os','-ffreestanding','-fno-builtin','-Wall','-c',str(f),'-o',str(obj)],check=True)
subprocess.run([a.cross+'ld','-T',str(r.parent/'runtime/buffer.ld'),'-Map='+str(o/'test.map'),*objects,'-o',str(o/'test.elf')],check=True)
subprocess.run([a.cross+'objcopy','-O','binary',str(o/'test.elf'),str(o/'test.bin')],check=True)
with (o/'test.dis').open('w') as f:subprocess.run([a.cross+'objdump','-dr',str(o/'test.elf')],stdout=f,check=True)
(o/'build.json').write_text(json.dumps({'sha256':hashlib.sha256((o/'test.bin').read_bytes()).hexdigest(),'bytes':(o/'test.bin').stat().st_size,'sources':{str(f.relative_to(r.parent)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files+[r/'arena.h',r/'image.h',r.parent/'runtime/buffer.ld',r.parent/'runtime/buffer_io.h']}},indent=2)+'\n')
