#!/usr/bin/env python3
"""Offline relocation oracle for the complete private-library engine candidate."""
import argparse,hashlib,importlib.util,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--cross',required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('pack',Path(__file__).resolve().parent/'../relocate/pack.py');pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
obj=a.build/'doom-platform.o';raw=obj.read_bytes();blob,m=pack.rebase(raw,0,'_doom_engine_entry')
for base in (0x10000,0x200000,0xc02d0050):
 script=a.out/f'{base:x}.ld';script.write_text('ENTRY(_doom_engine_entry)\nSECTIONS { . = '+hex(base)+'; .text : { *(.text*) } . = ALIGN(16); .data : { *(.data*) *(.rodata*) } . = ALIGN(16); .bss : { *(.bss*) *(COMMON) } }\n')
 elf=script.with_suffix('.elf');binary=script.with_suffix('.bin');subprocess.run([a.cross+'ld','-T',str(script),str(obj),'-o',str(elf)],check=True);subprocess.run([a.cross+'objcopy','-O','binary',str(elf),str(binary)],check=True)
 assert binary.read_bytes()==pack.rebase(raw,base,'_doom_engine_entry')[0]
m.update(template_sha256=hashlib.sha256(blob).hexdigest(),object_sha256=hashlib.sha256(raw).hexdigest(),linker_addresses=[0x10000,0x200000,0xc02d0050],linker_match=True,executed_on_card=False,admitted=False)
(a.out/'template.bin').write_bytes(blob);(a.out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({k:v for k,v in m.items() if k!='relocations'},indent=2));print('relocations',len(m['relocations']))
