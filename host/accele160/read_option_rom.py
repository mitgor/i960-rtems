#!/usr/bin/env python3
"""Paired PCI option-ROM reads, not a full-flash dump or mailbox experiment."""
import argparse,fcntl,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'rtems/transport'))
from card_select import select
p=argparse.ArgumentParser();p.add_argument('--bdf',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
lock=open('/run/lock/i960-loadrun.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
identity=select(a.bdf,'accele160',driver='myrs');d=Path('/sys/bus/pci/devices')/a.bdf
# No arbitrary BDF overrides, BAR accesses, commands, unbind, or firmware writes.
a.out.mkdir(parents=True,exist_ok=False)
report=dict(card=identity,boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),attempts=[])
(a.out/'config-before.bin').write_bytes((d/'config').read_bytes())
(a.out/'resource.txt').write_text((d/'resource').read_text())
try:
 for n in range(2):
  row=dict(read=n);report['attempts'].append(row)
  try:
   select(a.bdf,'accele160',driver='myrs')
   (d/'rom').write_text('1')
   try:
    with (d/'rom').open('rb') as f:data=f.read(2*1024*1024)
    (a.out/f'option-rom-{n}.bin').write_bytes(data)
    row.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),signature=data[:2].hex())
   finally:(d/'rom').write_text('0')
  except OSError as e:row.update(error=str(e),errno=e.errno)
finally:
 (a.out/'config-after.bin').write_bytes((d/'config').read_bytes())
 report['card_after']=select(a.bdf,'accele160',driver='myrs')
 (a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
