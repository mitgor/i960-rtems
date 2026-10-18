#!/usr/bin/env python3
"""Bounded READIMAGE observation using the exact initialized myrsread driver."""
import argparse,fcntl,hashlib,json,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'rtems/transport'))
from card_select import select,require_unbound_or_absent
p=argparse.ArgumentParser();p.add_argument('--bdf',required=True);p.add_argument('--module',required=True,type=Path);p.add_argument('--selector',type=int,required=True);p.add_argument('--length',type=int,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
# Bounds from the paired descriptor captured on this board. No arbitrary offset.
limits={1:65536,2:524288,3:28672,5:64512,9:1048576,14:1024}
if a.selector not in limits or a.length != ((limits[a.selector]+3)&~3):raise ValueError('outside verified image-size bounds')
lock=open('/run/lock/i960-loadrun.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
identity=select(a.bdf,'accele160',driver='myrsread')
require_unbound_or_absent('0000:37:04.1','dac960pg')
module_name=a.module.stem
if module_name not in ('companion','rawreader'):raise ValueError('unrecognized module identity')
if a.selector==9 and module_name!='rawreader':raise ValueError('whole flash requires separate rawreader')
if Path('/sys/module',module_name).exists():raise ValueError('previous read still owns resources')
# A retained failed allocation is allowed only after its command completed.
for other in ('accele-readimage','accele-rawreadimage'):
 status=Path('/sys/kernel/debug')/other/'status'
 if status.exists() and dict(x.split('=') for x in status.read_text().split()).get('done')!='1':
  raise ValueError('another READIMAGE command remains pending')
dev=Path('/sys/bus/pci/devices')/a.bdf
if list(dev.glob('host*/target*/*/block/*')):raise ValueError('card has block devices')
host,=dev.glob('host*/scsi_host/host*')
if not (host/'stock_descriptor').read_text().startswith('state=0 '):raise ValueError('descriptor job active')
a.out.mkdir(parents=True,exist_ok=False)
(a.out/'request.json').write_text(json.dumps(dict(card=identity,selector=a.selector,length=a.length,module_sha256=hashlib.sha256(a.module.read_bytes()).hexdigest(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()),indent=2)+'\n')
subprocess.run(['insmod',str(a.module),'bdf='+a.bdf,'selector='+str(a.selector),'length='+str(a.length)],check=True)
dbg=Path('/sys/kernel/debug')/('accele-rawreadimage' if module_name=='rawreader' else 'accele-readimage');start=time.monotonic()
while True:
 s=(dbg/'status').read_text()
 if s.startswith('done=1') or time.monotonic()-start>15:break
 time.sleep(.05)
(a.out/'status.txt').write_text(s);print(s,flush=True)
if not s.startswith('done=1'):raise RuntimeError('pending DMA retained; do not unload or unbind')
data=(dbg/'data.bin').read_bytes();(a.out/'data.bin').write_bytes(data)
fields=dict(x.split('=') for x in s.split())
if any(fields.get(k)!='0' for k in ('status','residual','guard_changes')) or len(data)!=a.length:
 raise RuntimeError('Uncertain transfer: DMA storage and module retained; do not unload')
(dbg/'release').write_text('release')
subprocess.run(['rmmod',module_name],check=True)
(a.out/'result.json').write_text(json.dumps(dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),elapsed=time.monotonic()-start,card_after=select(a.bdf,'accele160'),old_after=require_unbound_or_absent('0000:37:04.1','dac960pg')),indent=2)+'\n')
