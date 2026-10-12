#!/usr/bin/env python3
"""Verify preserved allocator-backed host output and i960 integration inventory."""
import argparse,hashlib,json,struct,tarfile
from pathlib import Path
assert __debug__, 'run without -O'
p=argparse.ArgumentParser();p.add_argument('artifacts',type=Path);p.add_argument('--reference',type=Path);a=p.parse_args();root=a.artifacts
reference=a.reference or root.parent/'doom-determinism-20261012'
for name,want in json.loads((root/'SHA256SUMS.json').read_text()).items():
 assert hashlib.sha256((root/name).read_bytes()).hexdigest()==want,name
with tarfile.open(root/'doom-host-builds.tar.gz') as t:
 rows=json.load(t.extractfile('host-final/results.json'));assert len(rows)==6
 assert {r['case'] for r in rows}=={f'p{p}-demo{d}-0' for p in (1,2) for d in (1,2,3)}
 exe=hashlib.sha256(t.extractfile('native-final/host32/doom-profile').read()).hexdigest()
 for row in rows:
  name=row['case'];expected=json.loads((reference/'runs'/name/'sha256-frames.json').read_text())
  actual=json.load(t.extractfile('host-final/'+name+'/sha256-frames.json'))
  assert len(actual)==2100 and actual==expected
  assert row['binary_sha256']==exe and row['frames']==2100 and row['matches_reference']
  assert 'reserved engine=655360' in row['drain']
  assert 'blocks=13;' in row['drain'] and not row['profile']['failed_allocations']
  log=t.extractfile('host-final/'+name+'/output.log').read().decode();assert row['drain'] in log
 data=t.extractfile('cross/i960/doom-engine.o').read()
 assert data[:6]==b'\x7fELF\x01\x01' and struct.unpack_from('<HH',data,16)==(1,19)
 off=struct.unpack_from('<I',data,32)[0];stride,count,strings=struct.unpack_from('<HHH',data,46)
 sections=[struct.unpack_from('<10I',data,off+i*stride) for i in range(count)]
 sh=sections[strings];names=data[sh[4]:sh[4]+sh[5]]
 sizes={names[s[0]:].split(b'\0')[0].decode():s[5] for s in sections if s[2]&2}
 assert sizes=={'.text':310960,'.data':69888,'.bss':250264}
 unresolved=[]
 for s in sections:
  if s[1]!=2:continue
  table=sections[s[6]];st=data[table[4]:table[4]+table[5]]
  for at in range(s[4],s[4]+s[5],s[9]):
   name,value,size,info,other,index=struct.unpack_from('<IIIBBH',data,at)
   if name and index==0:unresolved.append(st[name:].split(b'\0')[0].decode())
 expected=[l.split()[-1] for l in t.extractfile('cross/i960/undefined.txt').read().decode().splitlines()]
 assert sorted(unresolved)==sorted(expected) and len(unresolved)==53
 assert not set(unresolved)&{'_malloc','_calloc','_realloc','_free','_strdup'}
with tarfile.open(root/'live-evidence.tar.gz') as t:
 proof=json.load(t.extractfile('live/doom-heap.json'));assert proof['result'][2]==0 and proof['result'][5]==0x444c4942 and proof['retained_until_stop']==65536
assert (root/'http-headers.txt').read_text().startswith('HTTP/1.0 200 OK')
print(json.dumps(dict(host_frames=12600,engine_bytes=sum(sizes.values()),unresolved_imports=len(unresolved),allocation_imports_resolved=5,card_proof=True,http_restored=True),indent=2))
