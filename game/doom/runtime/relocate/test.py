#!/usr/bin/env python3
"""Compare our rebase byte-for-byte with three independent final links."""
import argparse,hashlib,json,struct,subprocess
from pathlib import Path
from pack import rebase
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--cross',default='/home/mit/i960/tools/bin/i960-coff-');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);r=Path(__file__).resolve().parent
subprocess.run([a.cross+'gcc','-mrp','-Os','-fno-builtin','-DI960_TARGET','-c',str(r/'probe.c'),'-o',str(a.out/'probe.o')],check=True)
blobs=[];raw=[]
for base in (0x10000,0x200000,0xc02d0050):
 script=a.out/f'{base:x}.ld';script.write_text('ENTRY(_relocated_entry)\nSECTIONS { . = '+hex(base)+'; .text : { *(.text*) } . = ALIGN(16); .data : { *(.data*) *(.rodata*) } . = ALIGN(16); .bss : { *(.bss*) *(COMMON) } }\n')
 elf=a.out/f'{base:x}.elf';subprocess.run([a.cross+'ld','--emit-relocs','-T',str(script),'-o',str(elf),str(a.out/'probe.o')],check=True)
 binary=elf.with_suffix('.bin');subprocess.run([a.cross+'objcopy','-O','binary',str(elf),str(binary)],check=True);raw.append(elf.read_bytes());blobs.append(binary.read_bytes())
finals=raw;raw=[(a.out/"probe.o").read_bytes()]
rebased,manifest=rebase(raw[0],0x200000);assert rebased==blobs[1] and rebase(raw[0],0x10000)[0]==blobs[0] and rebase(raw[0],0xc02d0050)[0]==blobs[2]
# Refuse geometry, architecture, stripped relocations, foreign types, duplicate
# records, and escaping addends. These cases may never become executable input.
cases=[]
def reject(label,blob,destination=0x200000):
 try:rebase(blob,destination)
 except (AssertionError,struct.error,UnicodeError):cases.append(label);return
 raise AssertionError('accepted '+label)
for label,offset,value in [('wrong_machine',18,3),('wrong_kind',16,2),('huge_sections',48,65535)]:
 b=bytearray(raw[0]);struct.pack_into('<H',b,offset,value);reject(label,b)
reject('truncated',raw[0][:100]);reject('misaligned_base',raw[0],3);reject('overflow_base',raw[0],0xfffffff0)
h=struct.unpack_from('<16sHHIIIIIHHHHHH',raw[0]);sections=[struct.unpack_from('<10I',raw[0],h[6]+i*40) for i in range(h[12])];rels=[s for s in sections if s[1]==9 and sections[s[7]][2]&2];assert rels
b=bytearray(raw[0]);struct.pack_into('<I',b,rels[0][4]+4,0xff);reject('foreign_relocation',b)
b=bytearray(raw[0]);address,info=struct.unpack_from('<II',b,rels[0][4]);target=sections[rels[0][7]];struct.pack_into('<I',b,target[4]+address-target[3],0x40000000);reject('escaping_addend',b)
b=bytearray(raw[0]);assert rels[0][5]>=16;b[rels[0][4]+8:rels[0][4]+16]=b[rels[0][4]:rels[0][4]+8];reject('duplicate',b)
b=bytearray(raw[0]);
for i,s in enumerate(sections):
 if s[1]==9:struct.pack_into('<I',b,h[6]+i*40+4,0)
reject('stripped_relocations',b)
manifest.update(sha256=hashlib.sha256(rebased).hexdigest(),linker_bytes_match_all_addresses=True,link_addresses=[0x10000,0x200000,0xc02d0050],final_emit_relocs_present=any(s[1]==9 for s in [struct.unpack_from("<10I",finals[0],struct.unpack_from("<I",finals[0],32)[0]+i*40) for i in range(struct.unpack_from("<H",finals[0],48)[0])]),negative_tests=cases,executed_on_card=False)
(a.out/'rebased.bin').write_bytes(rebased);(a.out/'result.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
