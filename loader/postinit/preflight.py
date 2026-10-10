#!/usr/bin/env python3
"""Read-only Linux PCI inventory for a future post-init loader test.
Reads sysfs metadata/configuration only: no MMIO, binding, config writes or commands.
This cannot verify on-card DMA/watchdog state or authorize flashing.
"""
import argparse
import json
import re
from pathlib import Path


def inspect(root, bdf):
    if not re.fullmatch(r'[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-7]', bdf):
        raise ValueError('full PCI BDF required')
    device=root/bdf
    def number(name): return int((device/name).read_text().strip(),16)
    if (number('vendor'),number('device')) != (0x1069,0x10):
        raise ValueError('not the tested 1069:0010 controller')
    data=(device/'config').read_bytes()
    if len(data)<128: raise ValueError('need at least 128 readable config bytes')
    def word(off,n=4):return int.from_bytes(data[off:off+n],'little')
    driver=(device/'driver').resolve().name if (device/'driver').exists() else None
    slots=(device/'resource').read_text().splitlines()
    start,end,flags=(int(x,16) for x in slots[0].split())
    module_loaded=Path('/sys/module/dac960dump').exists()
    return {'bdf':bdf,'driver':driver,'pci_command':word(4,2),
        'bar0':{'start':start,'end':end,'flags':flags,'size':end-start+1 if start else 0},
        'rom_bar':word(0x30),'rom_limit':word(0x74),'rom_translation':word(0x78),
        'primary_inbound_limit':word(0x40),'primary_inbound_translation':word(0x44),
        'dump_module_loaded':module_loaded,
        'host_preconditions_pass':driver is None and not module_loaded and start!=0 and end-start+1==0x2000 and bool(flags&0x200) and bool(word(4,2)&2),
        'read_only':True,'flash_ready':False,'custom_loader_execution_verified':False,
        'not_checked':['DMA registers (not mapped by PCI config)', 'external watchdog',
                       'recovery mechanism','cold-boot option-ROM suppression']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bdf',default='0000:37:09.1')
    a=p.parse_args()
    try:r=inspect(Path('/sys/bus/pci/devices'),a.bdf)
    except (OSError,ValueError) as e:p.error(str(e))
    print(json.dumps(r,indent=2))
    return 0 if r['host_preconditions_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
