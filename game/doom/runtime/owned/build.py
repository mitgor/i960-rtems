#!/usr/bin/env python3
"""Reviewed i960 non-local exit probe, using pinned unmodified machine assembly."""
import argparse,hashlib,importlib.util,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--cross',required=True);p.add_argument('--newlib',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);r=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pack',r/'../relocate/pack.py');pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
objs=[]
for source in (r/'probe.c',a.newlib/'newlib/libc/machine/i960/setjmp.S'):
 obj=a.out/(source.stem+'.o');subprocess.run([a.cross+'gcc','-mrp','-Os','-ffreestanding','-fno-builtin','-DI960_TARGET','-I'+str(a.newlib/'newlib/libc/include'),'-c',str(source),'-o',str(obj)],check=True);objs.append(obj)
obj=a.out/'owned-probe.o';subprocess.run([a.cross+'ld','-r','-d','-o',str(obj),*map(str,objs)],check=True);raw=obj.read_bytes();blob,m=pack.rebase(raw,0,'_owned_entry')
assert len(blob)<4096 and len(m['sections'])==3
nm=subprocess.check_output([a.cross+'nm',str(obj)],text=True);offset=int(next(row.split()[0] for row in nm.splitlines() if row.split()[-1]=='_owned_result'),16)+m['sections'][2]['offset'];assert offset+32<=m['memory_bytes']
for base in (0x10000,0x200000,0xc02d0050):
 script=a.out/f'{base:x}.ld';script.write_text('ENTRY(_owned_entry)\nSECTIONS { . = '+hex(base)+'; .text : { *(.text*) } . = ALIGN(16); .data : { *(.data*) *(.rodata*) } . = ALIGN(16); .bss : { *(.bss*) *(COMMON) } }\n');elf=script.with_suffix('.elf');binary=script.with_suffix('.bin');subprocess.run([a.cross+'ld','-T',str(script),str(obj),'-o',str(elf)],check=True);subprocess.run([a.cross+'objcopy','-O','binary',str(elf),str(binary)],check=True);assert binary.read_bytes()==pack.rebase(raw,base,'_owned_entry')[0]
m.update(sha256=hashlib.sha256(blob).hexdigest(),result_offset=offset,setjmp_source_sha256=hashlib.sha256((a.newlib/'newlib/libc/machine/i960/setjmp.S').read_bytes()).hexdigest())
(a.out/'template.bin').write_bytes(blob);(a.out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
s='static const unsigned char owned_probe_bytes[]={'+','.join(map(str,blob))+'};\nstatic const unsigned owned_probe_sites[]={'+','.join(map(str,m['relocations']))+'};\n'
s+='static const unsigned owned_geometry[][4]={'+','.join('{'+','.join(str(row[k]) for k in ('offset','file_bytes','memory_bytes','flags'))+'}' for row in m['sections'])+'};\n'
s+=f'#define OWNED_ENTRY {m["entry"]}u\n#define OWNED_RESULT {offset}u\n'
(a.out/'owned_probe_bytes.h').write_text(s)
with (a.out/'disassembly.txt').open('w') as f:subprocess.run([a.cross+'objdump','-dr',str(obj)],stdout=f,check=True)
print(json.dumps(m,indent=2))
