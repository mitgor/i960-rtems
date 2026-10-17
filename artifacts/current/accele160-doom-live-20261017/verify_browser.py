#!/usr/bin/env python3
"""Replay new-card HTTP frame/input acceptance and full flash read audits."""
import hashlib,json,struct
from pathlib import Path

root=Path(__file__).resolve().parent
case=root/'browser-1'
run=case/'run';persist=run/'persist';http=case/'http'
stock='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
def sha(data):return hashlib.sha256(data).hexdigest()
def fnv(data):
    h=0x811c9dc5
    for byte in data:h=((h^byte)*0x01000193)&0xffffffff
    return h
result=json.loads((run/'result.json').read_text())
web=json.loads((http/'result.json').read_text())
receipts=json.loads((persist/'live-frame-receipts.json').read_text())
reads=json.loads((persist/'engine-reads.json').read_text())
oracle=(root.parent/'accele160-doom-first-frame-20261017'/'native-requests.bin').read_bytes()
assert len(reads)==result['engine_wad_reads']==5045 and len(oracle)==5043*8
for i,row in enumerate(reads[:5043]):
    assert (row['offset'],row['n'])==struct.unpack_from('<II',oracle,8*i)
assert len(receipts)==len(web['frames'])==32
assert web['key_down'] and web['key_up']
assert result['firmware_sha256']==stock and result['old']['driver'] is None
assert result['card']['bdf']=='0000:37:09.1'
bygen={x['generation']:x for x in receipts}
assert sorted(bygen)==list(range(1,33))
epochs=set()
for entry in web['frames']:
    gen=entry['generation'];receipt=bygen[gen]
    packet=(http/f'http-frame-{gen:04d}.bin').read_bytes()
    header=struct.unpack_from('<8I',packet)
    assert header==(0x31424644,1,entry['epoch'],gen,320,200,65536,0)
    assert len(packet)==entry['bytes']==65568
    epochs.add(entry['epoch'])
    payload=packet[32:]
    assert sha(payload)==entry['sha256']==receipt['sha256']
    assert f'0x{fnv(payload):08x}'==receipt['fnv']
    assert payload==(persist/'live-frames'/f'frame-{gen:04d}.bin').read_bytes()
    assert receipt['slot']==((gen-1)&1)
assert len(epochs)==1
page=(persist/'quiescent-page.bin').read_bytes()
live=struct.unpack_from('<16I',page,0xd00)
assert live[:2]==(0x3145564c,0x161610e1)
assert live[10]==live[12]==2 and live[11]==173
assert struct.unpack_from('<II',page,0xb54)==(0x45495551,0)
assert struct.unpack_from('<I',page,0xcc0+14*4)[0]==0
for stage in ('pre','post'):
    boot=None
    for i in (0,1):
        audit=case/f'{stage}-{i}'
        req=json.loads((audit/'request.json').read_text())
        check=json.loads((audit/'result.json').read_text())
        assert req['selector']==9 and req['length']==1048576
        assert check['sha256']==stock and check['bytes']==1048576
        assert check['old_after']['driver'] is None
        assert (audit/'status.txt').read_text().strip()==(
            'done=1 status=0 residual=0 selector=9 length=1048576 '
            'released=0 guard_changes=0')
        if boot is None:boot=req['boot_id']
        else:assert boot==req['boot_id']
    if stage=='pre':assert boot==result['boot_id']
    else:assert boot!=result['boot_id']
print(f"accepted {len(web['frames'])} HTTP/card byte-identical frames, "
      'two acknowledged key events, paired pre/post flash audits; '
      f"{result['frame_timing']['render_fps']:.3f} card-side FPS")
