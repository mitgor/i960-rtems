#!/usr/bin/env python3
"""Build native test library or an absolute i960 segmented module; no upload."""
import argparse,subprocess,tarfile,sys,json,zlib,hashlib
from pathlib import Path
here=Path(__file__).resolve().parent;root=here.parents[2]
sys.path.insert(0,str(root/'rtems'));from lwip_patches import apply
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--tools',type=Path);p.add_argument('--newlib',type=Path);p.add_argument('--hello',action='store_true');p.add_argument('--base',type=lambda s:int(s,0),default=0xc0f50ca0);a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=True)
with tarfile.open(root/'artifacts/rtems-20261011/sources/lwip-2.1.3.tar.gz') as t:t.extractall(a.out,filter='data')
lw=a.out/'lwip-STABLE-2_1_3_RELEASE';apply(lw)
sources=sum((sorted((lw/'src/core'/d).glob('*.c')) for d in ('','ipv4','ipv6')),[])+[root/'rtems/net/network.c',root/'rtems/net/http.c',here/'net_module.c']
if a.hello:sources=[here/'hello_module.c']
flags=['-Os','-fno-builtin','-ffreestanding','-DACCELE_NET','-DI960_BACKGROUND_NET','-I'+str(root/'rtems/net'),'-I'+str(root/'rtems/transport'),'-I'+str(lw/'src/include')]
if not a.tools:
 subprocess.run(['cc','-shared','-fPIC',*flags,*map(str,sources),'-o',str(a.out/'network.so')],check=True);sys.exit(0)
if not a.newlib:p.error('--newlib include path required for i960')
flags+=['-mrp','-DI960_TARGET','-I'+str(a.newlib)]
objects=[]
for i,src in enumerate(sources+[root/'rtems/net/libc.c']):
 obj=a.out/f'{i:02}-{src.stem}.o';objects.append(obj)
 subprocess.run([str(a.tools/'i960-coff-gcc'),*flags,'-c',str(src),'-o',str(obj)],check=True)
ld=a.out/'module.ld';ld.write_text('ENTRY(_accele_net_entry)\nSECTIONS { . = 0x%x; .text : { *(.text*) *(.rodata*) . = ALIGN(16); __text_end = .; } .data : { *(.data*) . = ALIGN(16); } __file_end = .; .bss (NOLOAD) : { *(.bss*) *(COMMON) . = ALIGN(16); } __memory_end = .; ASSERT(. <= 0x%x,"module exceeds reserved partition") }\n'%(a.base,a.base+384*1024-32))
subprocess.run([str(a.tools/'i960-elf-ld'),'-T',str(ld),'-Map',str(a.out/'module.map'),'-o',str(a.out/'module.elf'),*map(str,objects)],check=True)
subprocess.run([str(a.tools/'i960-elf-objcopy'),'-O','binary',str(a.out/'module.elf'),str(a.out/'module.bin')],check=True)
nm=subprocess.check_output([str(a.tools/'i960-elf-nm'),'-n',str(a.out/'module.elf')],text=True);(a.out/'module.symbols').write_text(nm)
symbols={line.split()[2]:int(line.split()[0],16) for line in nm.splitlines() if len(line.split())==3}
b=(a.out/'module.bin').read_bytes();size=symbols['__file_end']-a.base;b=b.ljust(size,b'\0');(a.out/'module.bin').write_bytes(b)
# Logical RX text and RW initialized data/BSS. This CPU has no process page
# permissions. No ELF relocation at load.
m=dict(board=0x01601077,abi=1,base=a.base,entry=symbols['_accele_net_entry']-a.base,segments=[dict(offset=0,file_bytes=symbols['__text_end']-a.base,memory_bytes=symbols['__text_end']-a.base,flags=1,crc32=zlib.crc32(b[:symbols['__text_end']-a.base])),dict(offset=symbols['__text_end']-a.base,file_bytes=len(b)-(symbols['__text_end']-a.base),memory_bytes=symbols['__memory_end']-symbols['__text_end'],flags=2,crc32=zlib.crc32(b[symbols['__text_end']-a.base:]))],sha256=hashlib.sha256(b).hexdigest())
(a.out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(m,indent=2))
