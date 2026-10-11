#!/usr/bin/env python3
"""Read only four documented PCI configuration dwords; never touch BAR/MMIO.

No scanning, queue reads, APIC accesses or writes. Output is discovery evidence,
not authorization to use an apparently idle register or RAM location.
"""
import argparse,json,os,struct
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--device',default='0000:37:09.1');a=p.parse_args()
root=Path('/sys/bus/pci/devices')/a.device
if root.parent!=Path('/sys/bus/pci/devices') or not root.is_dir():p.error('invalid PCI device')
if (root/'vendor').read_text().strip()!='0x1069' or (root/'device').read_text().strip()!='0x0010':p.error('expected DAC960PG')
fd=os.open(root/'config',os.O_RDONLY)
try:
    result={}
    for name,offset in [('PIABAR',0x10),('PIALR',0x40),('PIATVR',0x44),('ATUCR',0x88)]:
        data=os.pread(fd,4,offset)
        if len(data)!=4:raise RuntimeError('short PCI config read')
        result[name]=f'0x{struct.unpack("<I",data)[0]:08x}'
finally:os.close(fd)
print(json.dumps(dict(device=a.device,registers=result,write_authorized=False),indent=2))
