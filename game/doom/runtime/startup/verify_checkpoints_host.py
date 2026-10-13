#!/usr/bin/env python3
"""Compare instrumented actual-engine native evidence with the N3 baseline."""
import argparse,hashlib,json,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();host=a.root/'platform-host';rows=[];normal=None
for i,mode in enumerate((0,1,2,3,0)):
 b=(host/f'startup-{i}.bin').read_bytes();ref=(a.baseline/f'startup-{i}.bin').read_bytes();trace=(host/f'startup-{i}.requests.bin').read_bytes();cp=(host/f'startup-{i}.checkpoints.bin').read_bytes();w=struct.unpack_from('<20I',b)
 assert b[:64]==ref[:64] and b[68:]==ref[68:] and trace==(a.baseline/f'startup-{i}.requests.bin').read_bytes()
 assert w[16]==struct.unpack_from('<I',ref,64)[0]+16400
 assert w[16]+900000+4352<8*1048576
 records=list(struct.iter_unpack('<8I',cp));assert records and len(records)<=512
 for j,r in enumerate(records):assert r[0:3]==(0x31504344,j+1,1) and 0<r[3]<=102
 assert records[0][3:]==(1,0,0,0,0) and records[-1][3]==62
 assert [r[3] for r in records[-3:]]==[60,61,62]
 assert records[-3][4]==w[11] and records[-2][4]==w[11]
 log=(host/f'startup-{i}.log').read_bytes();assert b'ERROR: AddressSanitizer' not in log and b'runtime error:' not in log
 if not mode:
  assert len(records)*2+5<512 and len(trace)==4747*8 and len(b)==64848
  if normal is None:normal=(b,trace,cp)
  else:assert normal==(b,trace,cp)
 rows.append(dict(mode=mode,reference_pixels_results_and_requests_identical=True,checkpoint_records=len(records),checkpoints_sha256=hashlib.sha256(cp).hexdigest(),peak_heap_with_checkpoint=w[16]))
build=json.loads((host/'build.json').read_text());assert build['sanitized'] and build['checkpoints']
flags=json.loads((a.root/'engine-host/host32/build.json').read_text())['flags'];assert '-fsanitize=address' in flags
m=json.loads((a.root/'admission/manifest.json').read_text());assert m['linker_match'] and m['admission_bytes']<=900000
assert hashlib.sha256(normal[1]).hexdigest()==m['startup']['requests_sha256'] and hashlib.sha256(normal[2]).hexdigest()==m['startup']['checkpoints_sha256']
assert (a.root/'admission/startup-checkpoints.bin').read_bytes()==normal[2]
cross=json.loads((a.root/'platform-cross/build.json').read_text());assert cross['final_link_passed'] and not cross['undefined'] and cross['checkpoints']
out=dict(host_only=True,cases=rows,checkpoint_allocation_bytes=16400,image_reservation=900000,target_staging=4352,admission_bytes=m['admission_bytes'])
a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
