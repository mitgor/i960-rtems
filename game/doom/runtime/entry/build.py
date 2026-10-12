#!/usr/bin/env python3
"""Build the reviewed runtime probe; require location-independent bytes."""
import argparse,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--cross',default='/home/mit/i960/tools/bin/i960-coff-');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);r=Path(__file__).resolve().parent
subprocess.run([a.cross+'gcc','-DI960_TARGET','-mrp','-Os','-ffreestanding','-fno-builtin','-c',str(r/'probe.c'),'-o',str(a.out/'runtime-probe.o')],check=True)
images=[]
for address in (0,0x100000):
 script=a.out/f'probe-{address:x}.ld';script.write_text('ENTRY(_doom_runtime_probe)\nSECTIONS { . = '+hex(address)+'; .text : { *(.text*) } .data : { *(.data*) *(.rodata*) *(.bss*) *(COMMON) } ASSERT(SIZEOF(.data)==0,"probe must have no static data") }\n')
 elf=a.out/f'probe-{address:x}.elf';binary=elf.with_suffix('.bin')
 subprocess.run([a.cross+'ld','-T',str(script),'-o',str(elf),str(a.out/'runtime-probe.o')],check=True)
 subprocess.run([a.cross+'objcopy','-O','binary',str(elf),str(binary)],check=True);images.append(binary.read_bytes())
assert images[0]==images[1] and 0<len(images[0])<=4096 and not len(images[0])%4
undefined=subprocess.check_output([a.cross+'nm','-u',str(a.out/'runtime-probe.o')],text=True);assert not undefined.strip()
(a.out/'runtime_probe_bytes.h').write_text('static const unsigned char runtime_probe_bytes[]={'+','.join(str(b) for b in images[0])+'};\n')
(a.out/'runtime-probe.bin').write_bytes(images[0])
(a.out/'runtime-probe.json').write_text(json.dumps(dict(bytes=len(images[0]),sha256=hashlib.sha256(images[0]).hexdigest(),identical_link_addresses=[0,0x100000],undefined=[]),indent=2)+'\n')
with (a.out/'runtime-probe.dis').open('w') as f:subprocess.run([a.cross+'objdump','-dr',str(a.out/'runtime-probe.o')],stdout=f,check=True)
