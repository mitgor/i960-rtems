#!/usr/bin/env python3
"""Read only known MU status/mailbox registers after the owner has failed.
No mailbox request, doorbell acknowledgement, config write or reset.
"""
import json,mmap,os,struct
fd=os.open('/sys/bus/pci/devices/0000:37:09.1/resource0',os.O_RDONLY)
with mmap.mmap(fd,4096,flags=mmap.MAP_SHARED,prot=mmap.PROT_READ) as m:
 print(json.dumps({hex(off):hex(struct.unpack_from('<I',m,off)[0]) for off in (0x10,0x14,0x18,0x1c,0x20,0x24,0x28,0x30,0x34)},indent=2))
os.close(fd)
