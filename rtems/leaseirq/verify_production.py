#!/usr/bin/env python3
"""Verify actual production close/open and same-boot restoration evidence."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import ROM_SHA,verify_close
root=Path(sys.argv[1]);verify_close(root/'production-close');out=root/'http-after-leaseirq';r=json.loads((out/'request.json').read_text())
boots={json.loads(p.read_text())['boot_id'] for p in root.glob('leaseirq-*/*/request.json')};assert boots=={r['boot_id']} and r['autonomous']
a=(out/'open/stage-before-a5.bin').read_bytes();assert a==(out/'open/stage-before-5a.bin').read_bytes() and len(a)==524288 and hashlib.sha256(a).hexdigest()==ROM_SHA
assert 'experiment-result=0 pending=0;' in (out/'preflight/result.txt').read_text()
assert 'SESSION OPEN ready; original saved; no user callback armed' in (out/'open/result.txt').read_text()
state=(root/'evidence/service-state.txt').read_text();assert 'active\n' in state and r['boot_id'] in state and 'drivers/dac960auto' in state and 'test-module-absent' in state
http=(root/'evidence/http-restored.txt').read_text();assert 'HTTP/1.0 200 OK' in http and 'Darth Vader' in http
print('All lease sessions and restored production share boot',r['boot_id'])
print('Current pre-test production close, new preflight, original paired OPEN, test-module absence and IPv6 HTTP 200 from Mac verified.')
print('Production payload',r['payload_sha256']);print('Production module',r['module_sha256'])
