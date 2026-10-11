#!/usr/bin/env python3
"""Replay terminal exception evidence without trusting the local result summary."""
import argparse,gzip,hashlib,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
import wire
from run import ROM_SHA
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('run',type=Path);a=p.parse_args();root=a.root;out=a.run
identity=json.loads((out/'request.json').read_text());code=(root/'residentnet/kernel.bin').read_bytes()
assert hashlib.sha256(code).hexdigest()==identity['payload_sha256'] and hashlib.sha256(wire.prepare(code)).hexdigest()==identity['image_sha256']
assert any(hashlib.sha256(p.read_bytes()).hexdigest()==identity['module_sha256'] for p in root.glob('residentnet-module*/dac960auto.ko'))
original=(out/'open/stage-before-a5.bin').read_bytes();assert hashlib.sha256(original).hexdigest()==ROM_SHA and original==(out/'open/stage-before-5a.bin').read_bytes()
raw=gzip.decompress((out/'trace.bin.gz').read_bytes());ns,n=struct.unpack_from('<QI',raw);assert ns>0 and n==16 and len(raw)==672
req=raw[12:28];arm=struct.unpack('<4I',req);assert arm[:2]==(0x31415452,1) and arm[3]==2|(1200<<8);epoch=arm[2]
audit=gzip.decompress((out/'audit-000001.bin.gz').read_bytes());before=wire.prepare(code)[:wire.bio.OFFSET]+wire.block(req,1)+original[wire.bio.IMAGE_SIZE:]
assert wire.response(before,audit+original[len(audit):])==(0,raw[32:])
flags=json.loads((root/'residentnet/build.json').read_text())['flags'];assert '-DI960_FAULT_OWNER' in flags
heap_test=next((int(f.split('=')[1]) for f in flags if f.startswith('-DI960_HEAP_TEST=')),0)
kind=4 if heap_test else 1 if '-DI960_FAULT_TEST=1' in flags else 2 if '-DI960_FAULT_TEST=3' in flags else 3
assert heap_test or any('-DI960_FAULT_TEST='+str(i) in flags for i in (1,2,3))
w=json.loads((out/'fault.json').read_text());assert len(w)==64 and w[:3]==[0x31464d4e,epoch,kind]
symbols={l.split()[2]:int(l.split()[0],16) for l in (root/'residentnet/kernel.symbols').read_text().splitlines() if len(l.split())==3}
assert w[9]==w[12]==symbols['_exclusive_nmi_entry'] and w[11]==symbols['_exclusive_fault_entry']
assert w[10]==symbols['_exclusive_exception_area']+64 and w[13]==0xc004e190
assert w[16:20]==[1,1,1,0] and w[20:26]==[0]*6 and w[26:30]==[2,0,0x242,0x13ffc] and w[31]==0
if kind==1:assert w[6]&0xffffff==0x50001 and w[7]==symbols['_exclusive_raise_fault']+4
elif kind in (3,4):assert w[4:8]==[0]*4
else:
 assert w[6]==248
 assert w[37]&0x80000000 and w[38]==0x1f3 and w[39]&8
 assert json.loads((out/"nmi-trigger.json").read_text())==[1,epoch,0,1,0,0,0,0]
extra='-DI960_EXTRA_RAM' in flags
if extra:assert w[40:47]==[4,262144,0,0,0,0,1]
if heap_test:
 assert '-DI960_GENERAL_HEAP' in flags and w[48:52]==[0x31504548,0xc022ee80,171824 if '-DI960_QUEUE_RECLAIM' in flags else 69952,1] and w[63]==heap_test
 assert w[52]=={1:1,2:3,3:2,4:2,5:1,6:2}[heap_test] and w[62]==(4 if heap_test==1 else 0)
 assert w[53]>w[54] and w[55]>0 and w[58:60]==[1,0] and w[60]>0 and w[61]>0
snapshots=[];cur=None
for e in json.loads((out/'controls.json').read_text()):
 v=e['words'];assert v[3]==1 and v[6:]==[0,0] and not v[4]&1
 assert v[5]=={4:0x8b000000,5:0x92000000|(e['arg']<<16),6:0x94000000,7:0x95000000}[e['op']]|epoch
 if e['op']==7:
  if cur is not None:assert cur==w;snapshots.append(cur)
  cur=[]
 elif e['op']==5:assert e['arg']==len(cur);cur.append(v[2])
assert cur==w; snapshots.append(cur);assert len(snapshots)==2
log=(out/'retained-close/result.txt').read_text();assert 'retained' in log.lower() or 'EBUSY' in log
print(json.dumps(dict(boot=identity['boot_id'],kind=kind,real_processor_fault=kind==1,physical_nmi_tested=kind==2,stable_snapshots=len(snapshots),fault_record=[hex(x) for x in w[3:8]],ownership_valid=True,scsi_reset_held=True,broader_ram_owned=extra,ram_probe=w[40:48] if extra else None,heap_report=w[48:64] if heap_test else None),indent=2))
