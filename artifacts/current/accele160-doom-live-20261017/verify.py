#!/usr/bin/env python3
"""Replay the accepted odd-page Doom transport and paired firmware audits."""
import hashlib,json,struct
from pathlib import Path
root=Path(__file__).resolve().parent
run=root/'accepted-1'
persist=run/'persist'
result=json.loads((run/'result.json').read_text())
receipts=json.loads((persist/'live-frame-receipts.json').read_text())
reads=json.loads((persist/'engine-reads.json').read_text())
stock='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
assert result['firmware_sha256']==stock
assert result['old']['driver'] is None and result['card']['bdf']=='0000:37:09.1'
assert result['release']=='reboot-only' and result['grant_retained']
assert result['engine_wad_reads']==len(reads)==5045
oracle=(root.parent/'accele160-doom-first-frame-20261017'/'native-requests.bin').read_bytes()
assert len(oracle)==5043*8
for i,row in enumerate(reads[:5043]):
    assert (row['offset'],row['n'])==struct.unpack_from('<II',oracle,8*i)
def sha(b):return hashlib.sha256(b).hexdigest()
def fnv(b):
    h=0x811c9dc5
    for v in b:h=((h^v)*0x01000193)&0xffffffff
    return h
for name,key in (('kernel.bin','kernel_sha256'),('image.bin','image_sha256')):
    assert sha((run/'build'/name).read_bytes())==result[key]
assert len(receipts)==32
assert sorted(x['generation'] for x in receipts)==list(range(1,33))
by_gen={x['generation']:x for x in receipts}
for generation in range(1,33):
    rec=by_gen[generation]
    b=(persist/'live-frames'/f'frame-{generation:04d}.bin').read_bytes()
    assert len(b)==65536 and sha(b)==rec['sha256']
    assert f'0x{fnv(b):08x}'==rec['fnv']
    assert rec['slot']==(generation-1)&1
frame=(persist/'game-frame.bin').read_bytes()
assert frame==(persist/'live-frames/frame-0032.bin').read_bytes()
assert sha(frame)==result['game_frame_sha256']
ticks=struct.unpack_from('<32I',frame,64768)
receipt_ticks=[by_gen[i]['card_tick'] for i in range(1,33)]
# The receipt is sampled after odd-page staging and host ACK; the frame tail
# records DG_DrawFrame time. Both clocks must progress, but need not coincide.
assert all(receipt_ticks[i]>=ticks[i] for i in range(32))
assert all(receipt_ticks[i]>receipt_ticks[i-1] for i in range(1,32))
assert result['frame_timing']['elapsed_ticks']==ticks[-1]-ticks[0]
assert abs(result['frame_timing']['render_fps']-3100/(ticks[-1]-ticks[0]))<1e-12
page=(persist/'quiescent-page.bin').read_bytes()
assert struct.unpack_from('<II',page,0xb54)==(0x45495551,0)
assert struct.unpack_from('<I',page,0xcc0+14*4)[0]==0
assert struct.unpack_from('<2I',page,0xd00)==(0x3145564c,0x161610e1)
for stage in ('pre','post'):
    boot=None
    for i in (0,1):
        audit=run/f'{stage}-{i}'
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
print(f"accepted 32 verified frames, {len(reads)} WAD reads, "
      f"{result['frame_timing']['render_fps']:.3f} card-side FPS, "
      'paired pre/post flash and ownership audits')
