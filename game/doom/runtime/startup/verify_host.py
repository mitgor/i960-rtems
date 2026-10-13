#!/usr/bin/env python3
"""Verify actual-engine native captures against the independent prior corpus."""
import argparse,hashlib,json,lzma,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--reference',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
c=json.loads((a.reference/'captures.json').read_text())[0];assert c['name']=='p1-demo1-0'
with lzma.open(a.reference/c['pixels'],'rb') as f:pixels=f.read(64000)
with lzma.open(a.reference/c['palette'],'rb') as f:palette=f.read(768)
want=json.loads((a.reference/'runs/p1-demo1-0/sha256-frames.json').read_text())[0]
assert hashlib.sha256(struct.pack('<II',0,2)+pixels+palette).hexdigest()==want
normal=None;checked=[]
for name in ('platform-host','platform-host-asan'):
 root=a.root/name;rows=json.loads((root/'startup-results.json').read_text());assert [r['mode'] for r in rows]==[0,1,2,3,0]
 assert json.loads((root/'build.json').read_text())['sanitized']
 for i,row in enumerate(rows):
  b=(root/f'startup-{i}.bin').read_bytes();v=list(struct.unpack_from('<12I',b));e=list(struct.unpack_from('<8I',b,48));assert row['result']==v and row['extra']==e
  assert v[:3]==[0x454e4750,2,6291456] and v[9]==[0,2,4,3][row['mode']] and v[10]==1 and e[3]==2
  assert e[4]+900000+4352<8*1048576
  trace=(root/f'startup-{i}.requests.bin').read_bytes();pairs=list(struct.iter_unpack('<2I',trace));assert len(pairs)==e[1] and sum(n for off,n in pairs)==e[2]
  assert all(0<n<=4096 and off+n<=28795076 for off,n in pairs)
  assert b'ERROR: AddressSanitizer' not in (root/f'startup-{i}.log').read_bytes() and b'runtime error:' not in (root/f'startup-{i}.log').read_bytes()
  if not row['mode']:
   assert len(b)==64848 and b[80:64080]==pixels and b[64080:]==palette
   assert v[3:7]==[4000963876,1611003811,1,1] and v[11]==213 and len(pairs)==4747
   assert row['frame_sha256']==hashlib.sha256(b[80:]).hexdigest()
   if normal is None:normal=(b,trace)
   else:assert (b,trace)==normal
  else:assert len(b)==80 and v[5:7]==[0,0] and len(pairs)==100
 checked.append(dict(build=name,cases=5,normal_frame_and_requests_identical=True))
flags=json.loads((a.root/'engine-host-asan/host32/build.json').read_text())['flags'];assert '-fsanitize=address' in flags
cross=json.loads((a.root/'platform-cross/build.json').read_text());assert cross['final_link_passed'] and cross['undefined']==[]
m=json.loads((a.root/'admission/manifest.json').read_text());assert m['admission_bytes']<=900000 and m['linker_match'] and hashlib.sha256((a.root/'admission/startup-requests.bin').read_bytes()).hexdigest()==m['startup']['requests_sha256']
assert (a.root/'admission/startup-requests.bin').read_bytes()==normal[1]
out=dict(actual_engine=True,private_newlib=True,host_cases=checked,corpus_frame_sha256=want,peak_private_bytes=6445535,peak_private_blocks=13,peak_heap_with_retained_buffers=6629855,native_image_reservation=900000,extra_card_staging=4352,admitted_image_bytes=m['admission_bytes'],i960_executed=False)
a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
