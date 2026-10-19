#!/usr/bin/env python3
"""Read identified PCI config and the existing console; never map BARs or write PCI."""
import json,os,subprocess,time
from pathlib import Path

def command(*args):
    return subprocess.check_output(args,text=True,timeout=15).strip()

def capture():
    devices={}
    for bdf,identity in [('0000:37:09.0',(0x8086,0x2962)),('0000:37:09.1',(0x1069,0x50))]:
        path=Path('/sys/bus/pci/devices')/bdf
        actual=tuple(int((path/k).read_text(),16) for k in ('vendor','device'))
        if actual!=identity:raise ValueError('PCI identity changed: '+bdf)
        with (path/'config').open('rb',buffering=0) as f:
            header=f.read(64)
            if len(header)!=64:raise ValueError('short configuration header')
            # 80303 bridge SACR, documented PCI config 4c; ordinary RW register.
            sacr=None
            if bdf.endswith('.0'):
                f.seek(0x4c);sacr=f.read(4)
                if len(sacr)!=4:raise ValueError('short SACR')
        devices[bdf]=dict(config=header.hex(),sacr=None if sacr is None else sacr.hex(),
            driver=os.path.basename(os.path.realpath(path/'driver')) if (path/'driver').exists() else None)
    return dict(boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        monotonic=time.monotonic(),devices=devices,
        apps=command('/home/mit/rtems-console','apps'),
        mem=command('/home/mit/rtems-console','mem'),
        uptime=command('/home/mit/rtems-console','uptime'),
        services=command('systemctl','is-active','i960-doom.service','i960-doom-stream.service'))

if __name__=='__main__':
    rows=[]
    for i in range(3):
        rows.append(capture())
        if i<2:time.sleep(1)
    print(json.dumps(dict(schema=1,samples=rows),indent=2))
