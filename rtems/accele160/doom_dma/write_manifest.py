#!/usr/bin/env python3
"""Bind exact board kernel, optimized engine, host pin module and validator."""
from pathlib import Path
import hashlib,json,sys
src,build,engine,module=map(Path,sys.argv[1:])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
x=(build/'image.bin').read_bytes();h=2166136261
for v in x:h=((h^v)*16777619)&0xffffffff
persistent=json.loads(engine.read_text()).get("persistent_play",False)
if persistent:
 assert json.loads((build/'build.json').read_text())['persistent'], 'persistent kernel required'
m=dict(frames=0 if persistent else 32,persistent=persistent,card_profile="accele160",source_sha256=sha(src/'app.c'),kernel_sha256=sha(build/'kernel.bin'),image_sha256=sha(build/'image.bin'),image_fnv=f'0x{h:08x}',engine_manifest_sha256=sha(engine),dma_module_sha256=sha(module))
for name,key in [('fnv_host.so','native_fnv_sha256'),('frame_dma.h','dma_source_sha256'),('copy.h','copy_sha256'),('engine_identity.h','engine_identity_sha256')]:m[key]=sha(src/name)
(src/('persistent-manifest.json' if persistent else 'live-32-manifest.json')).write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(m,indent=2))
