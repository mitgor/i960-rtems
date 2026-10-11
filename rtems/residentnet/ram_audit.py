#!/usr/bin/env python3
"""Link-image ownership audit. Describes only the existing allocated interval."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('build',type=Path);a=p.parse_args();symbols=[]
for l in (a.build/'kernel.symbols').read_text().splitlines():
 fields=l.split()
 if len(fields)==3:symbols.append((int(fields[0],16),fields[1],fields[2]))
byname={name:address for address,kind,name in symbols}
lo,hi=0xc0f4c010,0xc0f9bff0
assert byname['_start']==0xc0f2c000
assert lo<=byname['__bss_start']<=byname['__bss_end']<hi
for address,kind,name in symbols:
 if kind in 'bBdD':assert lo<=address<hi,(name,hex(address))
 if kind in 'tT':assert 0xc0f2c000<=address<0xc0f4c000,(name,hex(address))
for name in ['_workspace','_stacks','_switch_irq_areas','_netlink']:assert lo<=byname[name]<hi
print(json.dumps(dict(payload_sha256=hashlib.sha256((a.build/'kernel.bin').read_bytes()).hexdigest(),mutable_low=hex(lo),mutable_high_exclusive=hex(hi),bss_start=hex(byname['__bss_start']),bss_end=hex(byname['__bss_end']),unused_mutable_tail=hi-byname['__bss_end'],symbol_count=len(symbols),objects={n:hex(byname[n]) for n in ['_workspace','_stacks','_switch_irq_areas','_netlink']},broader_ram_owned=False,regions=[['c0000000','c0f2c000','unreclaimed firmware/unknown'],['c0f2c000','c0f4c000','immutable upload code'],['c0f4c000','c0f4c010','lower guard'],['c0f4c010','c0f9bff0','owned mutable upload'],['c0f9bff0','c0f9c000','upper guard'],['c0f9c000','c0f9f060','BIO transport'],['c0f9f060','c0fac000','saved upload tail; do not reclaim'],['c0fac000','c1000000','outside upload allocation; no new ownership']]),indent=2))
