#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import verify_close,ROM_SHA
r=Path(sys.argv[1]);e=Path(sys.argv[2]);verify_close(r/'http-after-handoff-final/close')
p=r/'http-after-exclusive';identity=json.loads((p/'request.json').read_text());assert identity['autonomous']
a=(p/'open/stage-before-a5.bin').read_bytes();assert a==(p/'open/stage-before-5a.bin').read_bytes() and len(a)==524288 and hashlib.sha256(a).hexdigest()==ROM_SHA
assert 'experiment-result=0 pending=0;' in (p/'preflight/result.txt').read_text()
assert 'SESSION OPEN ready; original saved; no user callback armed' in (p/'open/result.txt').read_text()
boot=(e/'reboot-after-stop.txt').read_text().splitlines()[0];assert boot==identity['boot_id'] and boot!=(e/'reboot-after-cap.txt').read_text().splitlines()[0]
assert 'module-absent' in (e/'reboot-after-stop.txt').read_text() and 'unbound' in (e/'reboot-after-stop.txt').read_text()
s=(e/'service-state.txt').read_text();assert 'active' in s and boot in s and 'drivers/dac960auto' in s
h=(e/'http-restored.txt').read_text();assert 'HTTP/1.0 200 OK' in h and 'Darth Vader' in h
print('Pre-test production close, fresh boot, original paired RAM, production OPEN, active service and IPv6 HTTP 200 from Mac verified.')
print(json.dumps(identity,indent=2))
