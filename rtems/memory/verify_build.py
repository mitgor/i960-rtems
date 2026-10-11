#!/usr/bin/env python3
"""Verify preserved A/B/check build bytes, layout, source and check injection."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('artifacts',type=Path);a=p.parse_args()
root=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result={}
for variant in ['byte','word','check']:
 d=a.artifacts/variant
 meta=json.loads((d/'build.json').read_text());app=json.loads((d/'raycaster-build.json').read_text())
 assert sha(d/'kernel.bin')==meta['payload_sha256']
 assert (d/'kernel.bin').stat().st_size==meta['payload_bytes']<=0x6fff0
 assert '-fno-builtin' in meta['flags']
 assert app['memory']==('byte' if variant=='byte' else 'word')
 assert app['memory_check_batches']==(264 if variant=='check' else 0)
 for name,digest in app['source_sha256'].items():assert sha(d/'target-source'/name)==digest,name
 symbols={f[2]:int(f[0],16) for l in (d/'kernel.symbols').read_text().splitlines() if len(f:=l.split())==3}
 assert symbols['_start']==0xc0f2c000
 assert 0xc0f4c010<=symbols['__bss_start']<symbols['__bss_end']<=0xc0f9bff0
 assert all(symbols[n]<0xc0f4c000 for n in ['_memcpy','_memset','_ray_request'])
 assert ' U ' not in (d/'kernel.symbols').read_text()
 result[variant]=dict(payload_sha256=meta['payload_sha256'],payload_bytes=meta['payload_bytes'],source_hashes_verified=len(app['source_sha256']),bss_start=hex(symbols['__bss_start']),bss_end=hex(symbols['__bss_end']))
b=a.artifacts/'byte/target-source';w=a.artifacts/'word/target-source';c=a.artifacts/'check/target-source'
for f in b.iterdir():
 if f.name!='libc.c':assert f.read_bytes()==(w/f.name).read_bytes(),f.name
old=(b/'libc.c').read_text()
expected=(root/'rtems/memory/word.c').read_text()+'\n'+'\n'.join(l for l in old.splitlines() if not l.startswith(('void *memcpy(','void *memset(')))+'\n'
assert (w/'libc.c').read_text()==expected
for f in w.iterdir():
 if f.name!='app.c':assert f.read_bytes()==(c/f.name).read_bytes(),f.name
source=(w/'app.c').read_text()
source='#include "check.h"\nstatic unsigned int memory_batch;\n'+source
source=source.replace('  job=1;\n','  if(memory_batch<MEMORY_BATCHES){\n   if(memory_check_batch(memory_batch))bounded_fatal(0x60000+memory_batch);\n   memory_batch++;\n  }\n  job=1;\n')
assert (c/'app.c').read_text()==source
for name in ['check.c','check.h']:assert (c/name).read_bytes()==(root/'rtems/memory'/name).read_bytes()
assert result['byte']['payload_sha256']=='47046f511b683911df78a329985efba067836e982c0f42ec1a5d863e8d8242a5'
assert result['word']['bss_end']==result['byte']['bss_end']
print(json.dumps(result,indent=2))
