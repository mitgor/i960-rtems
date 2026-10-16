#!/usr/bin/env python3
"""Independent replay of every paired scalar capture and expected test corpus."""
import argparse,hashlib,json,re,sys
from pathlib import Path
from test import oracle
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'host/loadrun'))
from loadrun import verify
p=argparse.ArgumentParser();p.add_argument('probe',type=Path);a=p.parse_args();d=a.probe
m=json.loads((d/'build.json').read_text());payload=(d/'probe.bin').read_bytes();module=(d/'module/dac960loadrun.ko').read_bytes();boots=set()
body=(d/'candidate-text.bin').read_bytes();offset=m['candidate_text_offset']
assert len(body)==m['candidate_text_bytes'] and hashlib.sha256(body).hexdigest()==m['candidate_text_sha256'] and payload[offset:offset+len(body)]==body
assert m['batches']==32 and m['per_batch']==32 and len(m['vectors'])==1024 and m['candidate_linked_directly']
assert m['legacy_object_sha256']=='beb7a66306aef9fa8a0cb4c0e18e81524b337c05f640897282c3f8bedcc6dd1b'
for row in m['vectors']:assert oracle(row['values'])==row['expected']
for i in range(32):
 c=d/f'case-{i}';q=json.loads((c/'request.json').read_text());boots.add(q['boot_id'])
 assert q['payload_sha256']==hashlib.sha256(payload).hexdigest() and q['module_sha256']==hashlib.sha256(module).hexdigest()
 assert q['argument']==i and q['entry']==0 and q['buffer_io'] is False
 assert (c/'payload.bin').read_bytes()==payload and (c/'unloaded.txt').read_text()=='clean module unload completed\n'
 assert verify(c,payload)==32
 ids=[int(x) for x in re.findall(r'^submit op=[0-9a-f]+ id=(\d+) ',(c/'result.txt').read_text(),re.M)]
 assert ids==list(range(1,111))
assert len(boots)==1
print(json.dumps(dict(passed=True,transactions=32,vectors=1024,firmware_commands=3520,paired_staging_phases=96,clean_unload=True,boot_id=next(iter(boots)),candidate_object_sha256=m['candidate_object_sha256']),indent=2))
