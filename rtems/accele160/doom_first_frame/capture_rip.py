#!/usr/bin/env python3
"""Read the retained grant-owned interrupt sample page without unloading it."""
import argparse,fcntl,mmap,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'rtems/transport'))
from card_select import select
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--scan',action='store_true')
a=p.parse_args()
lock=open('/run/lock/i960-loadrun.lock','w')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
bdf='0000:37:09.1'
select(bdf,'accele160',driver='myrsread')
assert select('0000:37:04.1','dac960pg')['driver'] is None
assert Path('/sys/module/admit_command').exists()
dev=Path('/sys/bus/pci/devices')/bdf
with (dev/'config').open('r+b',buffering=0) as cfg,(dev/'resource0').open('r+b',buffering=0) as res:
    bar=mmap.mmap(res.fileno(),8192)
    try:
        cfg.seek(0x44);original=struct.unpack('<I',cfg.read(4))[0]
        assert original==0xc0000000,hex(original)
        try:
            pages={}
            addresses=(0xc076f000,0xc0770000,0xc0771000,0xc0772000,0xc0773000)
            for addr in addresses if a.scan else (0xc0771000,):
                cfg.seek(0x44);cfg.write(struct.pack('<I',addr))
                cfg.seek(0x44);assert struct.unpack('<I',cfg.read(4))[0]==addr
                pages[addr]=bytes(bar[4096:8192])
            data=pages[0xc0771000]
        finally:
            cfg.seek(0x44);cfg.write(struct.pack('<I',original))
            cfg.seek(0x44);assert struct.unpack('<I',cfg.read(4))[0]==original
    finally:bar.close()
assert len(data)==4096
a.out.write_bytes(data)
words=struct.unpack('<1024I',data)
print('interrupts',words[0], 'latest',hex(words[1+(words[0]&511)]))
if a.scan:
    for addr,page in pages.items():
        print(hex(addr),*[hex(x) for x in struct.unpack_from('<4I',page)])
