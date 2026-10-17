#!/usr/bin/env python3
"""Read a retained AcceleRAID task lease without releasing anything."""
import argparse, fcntl, json, mmap, struct
from pathlib import Path

PAGE=4096
BDF='0000:37:09.1'
DEV=Path('/sys/bus/pci/devices')/BDF

def main():
    p=argparse.ArgumentParser()
    p.add_argument('out',type=Path)
    a=p.parse_args()
    lock=open('/run/lock/i960-loadrun.lock','w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    cfg=(DEV/'config').open('r+b',buffering=0)
    res=(DEV/'resource0').open('r+b',buffering=0)
    bar=mmap.mmap(res.fileno(),2*PAGE)
    cfg.seek(0x44);original=struct.unpack('<I',cfg.read(4))[0]
    if original!=0xc0000000:raise RuntimeError('PIATVR not stock')
    def snap(addr):
        cfg.seek(0x44);cfg.write(struct.pack('<I',addr))
        cfg.seek(0x44)
        if struct.unpack('<I',cfg.read(4))[0]!=addr:raise RuntimeError('PIATVR readback')
        return bytes(bar[PAGE:2*PAGE])
    try:
        a.out.mkdir(parents=True,exist_ok=False)
        for name,addr in (('page',0xc000e000),('isr0',0xc071f000),
                          ('isr1',0xc0721000),('owner',0xc0384000)):
            (a.out/(name+'.bin')).write_bytes(snap(addr))
        page=(a.out/'page.bin').read_bytes()
        stack=(a.out/'isr0.bin').read_bytes()
        record={'side':list(struct.unpack_from('<8I',page,0xa40)),
                'diag':list(struct.unpack_from('<8I',page,0xa60)),
                'trace':list(struct.unpack_from('<43I',stack,3072))}
        (a.out/'record.json').write_text(json.dumps(record,indent=2)+'\n')
        print(json.dumps(record,indent=2))
    finally:
        cfg.seek(0x44);cfg.write(struct.pack('<I',original))
        bar.close();res.close();cfg.close()

if __name__=='__main__':main()
