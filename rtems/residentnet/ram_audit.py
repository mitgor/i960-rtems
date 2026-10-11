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
# The new queue must fit as a whole object, not merely have an in-range start.
# Historical GCC may order arrays either way; use adjacent symbols for size.
ordered=sorted(set(address for address,kind,name in symbols if kind in 'bBdD'))
extra='-DI960_EXTRA_RAM' in json.loads((a.build/'build.json').read_text())['flags']
heap='-DI960_GENERAL_HEAP' in json.loads((a.build/'build.json').read_text())['flags']
if heap:
 assert extra
 for name in ('_blocks','_app_heap'):assert lo<=byname[name]<hi
 for name in ('_malloc','_calloc','_realloc','_free'):assert 0xc0f2c000<=byname[name]<0xc0f4c000
frame_start=byname['_internal_frames' if extra else '_frames'];next_address=min(x for x in ordered if x>frame_start)
frame_bytes=next_address-frame_start
layouts={8*1536:(8,1536),32*1536:(32,1536),64*1536:(64,1536),72*1500:(72,1500),68*1500:(68,1500)}
assert frame_bytes in layouts
assert lo<=frame_start and frame_start+frame_bytes<=hi
queue_slots,frame_capacity=layouts[frame_bytes]
print(json.dumps(dict(payload_sha256=hashlib.sha256((a.build/'kernel.bin').read_bytes()).hexdigest(),mutable_low=hex(lo),mutable_high_exclusive=hex(hi),bss_start=hex(byname['__bss_start']),bss_end=hex(byname['__bss_end']),unused_mutable_tail=hi-byname['__bss_end'],symbol_count=len(symbols),queue_slots=queue_slots,queue_bytes=frame_bytes,frame_capacity=frame_capacity,objects={n:hex(byname[n]) for n in ['_workspace','_stacks','_switch_irq_areas','_netlink']},broader_ram_owned=False,application_heap_candidate=dict(base="0xc022ee80",bytes=69952,requires_live_validation=True) if heap else None,external_queue_candidate=dict(base="0xc0200040",bytes=192000,requires_live_validation=True) if extra else None,regions=[['c0000000','c0f2c000','unreclaimed firmware/unknown'],['c0f2c000','c0f4c000','immutable upload code'],['c0f4c000','c0f4c010','lower guard'],['c0f4c010','c0f9bff0','owned mutable upload'],['c0f9bff0','c0f9c000','upper guard'],['c0f9c000','c0f9f060','BIO transport'],['c0f9f060','c0fac000','saved upload tail; do not reclaim'],['c0fac000','c1000000','outside upload allocation; no new ownership']]),indent=2))
