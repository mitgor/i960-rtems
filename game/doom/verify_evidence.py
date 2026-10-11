#!/usr/bin/env python3
"""Validate stored milestone-1 evidence without executing Linux or i960 binaries."""
import argparse,hashlib,json,struct,subprocess,sys,tarfile,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('artifacts',type=Path);a=p.parse_args();art=a.artifacts.resolve()
assert __debug__
for row in json.loads((art/'archive-hashes.json').read_text()):
 blob=(art/row['file']).read_bytes();assert len(blob)==row['bytes'] and hashlib.sha256(blob).hexdigest()==row['sha256']
with tempfile.TemporaryDirectory(prefix='doom-verify-') as tmp:
 root=Path(tmp)
 for name in ('doom-builds.tar.gz','doom-profiles.tar.gz'):
  with tarfile.open(art/name) as archive:archive.extractall(root,filter='data')
 for r in json.loads((art/'build-files.json').read_text()):assert hashlib.sha256((root/r['path']).read_bytes()).hexdigest()==r['sha256'],r['path']
 data=(root/'cross/i960/doom-engine.o').read_bytes()
 assert data[:6]==b'\x7fELF\x01\x01' and struct.unpack_from('<HH',data,16)==(1,19)
 off=struct.unpack_from('<I',data,32)[0];stride,count,strings=struct.unpack_from('<HHH',data,46)
 sections=[struct.unpack_from('<10I',data,off+i*stride) for i in range(count)]
 sh=sections[strings];names=data[sh[4]:sh[4]+sh[5]]
 sizes={names[s[0]:].split(b'\0')[0].decode():s[5] for s in sections if s[2]&2}
 assert sizes==json.loads((art/'summary.json').read_text())['engine_sections']
 symbol_names=[]
 for s in sections:
  if s[1]!=2:continue
  table=sections[s[6]];st=data[table[4]:table[4]+table[5]]
  for at in range(s[4],s[4]+s[5],s[9]):
   name,value,size,info,other,index=struct.unpack_from('<IIIBBH',data,at)
   if name and index==0:symbol_names.append(st[name:].split(b'\0')[0].decode())
 expected=[line.split()[-1] for line in (root/'cross/i960/undefined.txt').read_text().splitlines()]
 assert sorted(symbol_names)==sorted(expected)
 summary=json.loads(subprocess.check_output([sys.executable,str(Path(__file__).with_name('summarize.py')),str(root)],text=True))
 assert summary==json.loads((art/'summary.json').read_text())
 runs=json.loads((root/'profiles.json').read_text());assert len(runs)==20
 for r in runs:
  assert r==json.loads((root/'runs'/r['name']/'run.json').read_text())
  assert r['returncode']==0 and r['profile']['pointer_bytes']==4 and r['profile']['frames']==2100
  assert r['profile']['zone_reserved']==r['mb']*1048576 and r['profile']['zone_used_peak_including_headers']<=r['profile']['zone_reserved']
  assert r['profile']['failed_allocations']==0
 low=json.loads((root/'low-memory.json').read_text());assert len(low)==4
 for r in low:
  assert r['returncode']==255 and r['profile']['frames']==0
  assert 'Z_Malloc: failed on allocation' in (root/'low-memory'/r['name']/'output.log').read_text()
 a=(root/'fulltrace-1/frames.txt').read_text().splitlines();b=(root/'fulltrace-2/frames.txt').read_text().splitlines()
 repeat=dict(frames=len(a),initial_100_match=(root/'clear-1/frames.txt').read_bytes()==(root/'clear-2/frames.txt').read_bytes(),differing_frames=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y],full_match=a==b)
 assert len(a)==len(b)==2100 and repeat==json.loads((art/'repeatability.json').read_text())
 assert 'overflow failure pass' in (root/'test-profile.log').read_text()
 print(json.dumps(dict(i960_engine_verified=True,compiled_sources=summary['compiled_sources'],engine_bytes=sum(sizes.values()),unresolved_symbols=len(symbol_names),host_frames=summary['profiled_frames'],low_memory_failures=len(low),repeatability=repeat),indent=2))
