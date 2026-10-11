#!/usr/bin/env python3
"""Validate boot transition and restored production from saved evidence."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import ROM_SHA,verify_close
root=Path(sys.argv[1]);e=root/'evidence'
first=(e/'before-reboot.txt').read_text().splitlines()[0];second=(e/'after-reboot.txt').read_text().splitlines()[0];assert first!=second
for run,boot in [('persistirq-early-close',first),('persistirq-recovery',second)]:assert json.loads((root/run/'run-0/request.json').read_text())['boot_id']==boot
out=root/'http-after-persistirq';r=json.loads((out/'request.json').read_text());assert r['autonomous'] and r['boot_id']==second
one=(out/'open/stage-before-a5.bin').read_bytes();assert one==(out/'open/stage-before-5a.bin').read_bytes() and len(one)==524288 and hashlib.sha256(one).hexdigest()==ROM_SHA
assert 'experiment-result=0 pending=0;' in (out/'preflight/result.txt').read_text()
assert 'SESSION OPEN ready; original saved; no user callback armed' in (out/'open/result.txt').read_text()
state=(e/'service-state.txt').read_text();assert 'active\n' in state and 'drivers/dac960auto' in state and 'test-module-absent' in state and second in state
http=(e/'http-restored.txt').read_text();assert 'HTTP/1.0 200 OK' in http and 'Darth Vader' in http
verify_close(root/'production-close')
print('Distinct boots matched to actual requests:',first,second)
print('Pre-test production close verified; fresh autonomous preflight and original paired OPEN verified; active production and IPv6 HTTP 200 from Mac. No visitor logs exported.')
print('Production payload:',r['payload_sha256']);print('Production module:',r['module_sha256'])
