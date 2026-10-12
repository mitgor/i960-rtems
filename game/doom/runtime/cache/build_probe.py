#!/usr/bin/env python3
"""Trusted cache probe recipe, independently linked at three addresses."""
import argparse,hashlib,importlib.util,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--cross',required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);r=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pack',r/'../relocate/pack.py');pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
objs=[]
for name in ('probe','cache'):
 obj=a.out/(name+'.o');subprocess.run([a.cross+'gcc','-mrp','-Os','-ffreestanding','-fno-builtin','-DI960_TARGET','-c',str(r/(name+'.c')),'-o',str(obj)],check=True);objs.append(obj)
obj=a.out/'cache-probe.o';subprocess.run([a.cross+'ld','-r','-d','-o',str(obj),*map(str,objs)],check=True)
raw=obj.read_bytes();blob,m=pack.rebase(raw,0,'_cache_entry');assert len(m['sections'])==1 and m['sections'][0]['flags']==1 and len(blob)%4==0 and len(blob)<8192
for base in (0x10000,0x200000,0xc02d0050):
 script=a.out/f'{base:x}.ld';script.write_text('ENTRY(_cache_entry)\nSECTIONS { . = '+hex(base)+'; .text : { *(.text*) } . = ALIGN(16); .data : { *(.data*) *(.rodata*) } . = ALIGN(16); .bss : { *(.bss*) *(COMMON) } }\n')
 elf=script.with_suffix('.elf');binary=script.with_suffix('.bin');subprocess.run([a.cross+'ld','-T',str(script),str(obj),'-o',str(elf)],check=True);subprocess.run([a.cross+'objcopy','-O','binary',str(elf),str(binary)],check=True)
 assert binary.read_bytes()==pack.rebase(raw,base,'_cache_entry')[0]
m['sha256']=hashlib.sha256(blob).hexdigest();m['linker_addresses']=[0x10000,0x200000,0xc02d0050]
(a.out/'template.bin').write_bytes(blob);(a.out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
s='static const unsigned char cache_probe_bytes[]={'+','.join(map(str,blob))+'};\nstatic const unsigned int cache_probe_sites[]={'+','.join(map(str,m['relocations']))+'};\n#define CACHE_PROBE_ENTRY '+str(m['entry'])+'u\n'
(a.out/'cache_probe_bytes.h').write_text(s)
print(json.dumps(m,indent=2))
