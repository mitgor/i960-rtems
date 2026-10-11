#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import ROM_SHA,verify_close
p=Path(sys.argv[1])/'http-after-residentnet';e=Path(sys.argv[2]);prior=Path(sys.argv[3])/'http-after-transfer/close';verify_close(prior)
identity=json.loads((p/'request.json').read_text());assert identity['autonomous']
a=(p/'open/stage-before-a5.bin').read_bytes();assert a==(p/'open/stage-before-5a.bin').read_bytes() and hashlib.sha256(a).hexdigest()==ROM_SHA
assert 'experiment-result=0 pending=0;' in (p/'preflight/result.txt').read_text()
assert 'SESSION OPEN ready; original saved; no user callback armed' in (p/'open/result.txt').read_text()
boots=[(e/f'reboot-after-v{i}.txt').read_text().splitlines()[0] for i in (2,3,4)];assert len(set(boots))==3 and identity['boot_id']==boots[-1]
for i in (2,3,4):
 t=(e/f'reboot-after-v{i}.txt').read_text();assert 'module-absent' in t and 'unbound' in t
state=(e/'service-state.txt').read_text();assert boots[-1] in state and 'active' in state and 'drivers/dac960auto' in state
http=(e/'http-restored.txt').read_text();assert 'HTTP/1.0 200 OK' in http and 'Darth Vader' in http
print('Pre-batch close restored; three new boots; final original paired RAM and active production IPv6 HTTP 200 verified.')
print(json.dumps(identity,indent=2))
