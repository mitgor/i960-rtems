#!/usr/bin/env python3
"""Bind exact board kernel, optimized engine, host pin module and validator."""
from pathlib import Path
import hashlib,json,sys
if len(sys.argv) not in (5,6):raise SystemExit('usage: write_manifest.py SRC BUILD ENGINE DMA_MODULE [ADMIT_MODULE]')
src,build,engine,module=map(Path,sys.argv[1:5])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
x=(build/'image.bin').read_bytes();h=2166136261
for v in x:h=((h^v)*16777619)&0xffffffff
persistent=json.loads(engine.read_text()).get("persistent_play",False)
if persistent:
 assert json.loads((build/'build.json').read_text())['persistent'], 'persistent kernel required'
m=dict(reusable=json.loads((build/'build.json').read_text()).get('reusable',False),frames=0 if persistent else 32,persistent=persistent,card_profile="accele160",source_sha256=sha(src/'app.c'),kernel_sha256=sha(build/'kernel.bin'),image_sha256=sha(build/'image.bin'),image_fnv=f'0x{h:08x}',engine_manifest_sha256=sha(engine),dma_module_sha256=sha(module))
m['terminal_schema']=json.loads((build/'build.json').read_text()).get('terminal_schema',0)
m['terminal_test']=json.loads((build/'build.json').read_text()).get('terminal_test',0)
if m['terminal_schema']:
 m['terminal_sources']={name:sha(src.parent/'fault'/name) for name in ('policy.h','card.inc','terminal.S','host.py')}
m['service_schema']=json.loads((build/'build.json').read_text()).get('service_schema',0)
if m['service_schema']:
 m['service_sources']={name:sha(src.parent/'service'/name) for name in ('protocol.h','card.inc','host.py')}
m['keyboard_fifo_schema']=json.loads((build/'build.json').read_text()).get('keyboard_fifo_schema',0)
if m['keyboard_fifo_schema']:m['key_fifo_sha256']=sha(src/'key_fifo.h')
if len(sys.argv)==6:
 m['admit_module_sha256']=sha(Path(sys.argv[5]))
 m['admit_source_sha256']=sha(src.parents[2]/'host/accele160/ram_admit/admit_command.c')
for name,key in [('fnv_host.so','native_fnv_sha256'),('frame_dma.h','dma_source_sha256'),('copy.h','copy_sha256'),('engine_identity.h','engine_identity_sha256')]:m[key]=sha(src/name)
(src/('persistent-manifest.json' if persistent else 'live-32-manifest.json')).write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(m,indent=2))
