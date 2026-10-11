#!/usr/bin/env python3
"""Verify production closes, fresh original OPEN and external HTTP evidence."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import verify_close,ROM_SHA
root=Path(sys.argv[1]);evidence=Path(sys.argv[2])
for name in ('http-after-raycaster','http-after-handoff'):verify_close(root/name/'close')
p=root/'http-after-handoff-final';identity=json.loads((p/'request.json').read_text());assert identity['autonomous']
assert {json.loads(x.read_text())['boot_id'] for x in root.glob('handoff-v*-live/run-*/request.json')}=={identity['boot_id']}
a=(p/'open/stage-before-a5.bin').read_bytes();assert a==(p/'open/stage-before-5a.bin').read_bytes() and hashlib.sha256(a).hexdigest()==ROM_SHA
assert 'experiment-result=0 pending=0;' in (p/'preflight/result.txt').read_text()
assert 'SESSION OPEN ready; original saved; no user callback armed' in (p/'open/result.txt').read_text()
s=(evidence/'service-state.txt').read_text();assert 'active' in s and identity['boot_id'] in s and 'drivers/dac960auto' in s
h=(evidence/'http-restored.txt').read_text();assert 'HTTP/1.0 200 OK' in h and 'Darth Vader' in h
print('Previous and intermediate production closes verified. Final preflight and original paired OPEN verified. Same recovered boot as all five passing sessions. IPv6 HTTP 200 from Mac; production active.')
print(json.dumps(identity,indent=2))
