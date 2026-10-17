#!/usr/bin/env python3
"""Replay the new-card Doom WAD traces and completed post-reset audit."""
import gzip,hashlib,json,struct
from pathlib import Path

root=Path(__file__).resolve().parents[3]/'artifacts/current/accele160-doom-first-frame-20261017'
stock='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
oracle=(root/'native-requests.bin').read_bytes()
assert len(oracle)==5043*8
for attempt,count in [('attempt-1',1400),('attempt-2',3801)]:
    p=root/attempt
    reads=json.loads(gzip.decompress((p/'persist/engine-reads.json.gz').read_bytes()))
    assert len(reads)==count,(attempt,len(reads))
    for i,row in enumerate(reads):
        assert (row['offset'],row['n'])==struct.unpack_from('<II',oracle,8*i),(attempt,i)
        assert row['request_seq']==42+i,(attempt,i)
    page=(p/'persist/engine-final-page.bin' if attempt=='attempt-1' else
          p/'persist/engine-stall-page.bin').read_bytes()
    assert len(page)==4096
    wire=struct.unpack_from('<16I',page,0xc00)
    final_index=count if attempt=='attempt-1' else count-1
    assert wire[0]==42+final_index and wire[1:4]==(*struct.unpack_from('<II',oracle,8*final_index),1)
    assert wire[4]==wire[0] and wire[5:7]==wire[1:3] and wire[8:12]==(0,0,wire[7],wire[2])
    er=struct.unpack_from('<16I',page,0xc40)
    assert er[0:2]==(0x314d5246,1) and er[5]==0xffffffff
    assert er[14]==count if attempt=='attempt-2' else er[14]==0xffffffff
    print(attempt,'native requests and last WAD reply verified:',count)
for attempt in ('attempt-1','attempt-2','accepted'):
    post=root/attempt
    reqs=[json.loads((post/f'post-reset-{i}/request.json').read_text()) for i in range(2)]
    for i,req in enumerate(reqs):
        result=json.loads((post/f'post-reset-{i}/result.json').read_text())
        status=(post/f'post-reset-{i}/status.txt').read_text().strip()
        assert req['boot_id']==reqs[0]['boot_id'] and req['selector']==9 and req['length']==1048576
        assert req['card']['bdf']=='0000:37:09.1' and req['card']['driver']=='myrsread'
        assert result['bytes']==1048576 and result['sha256']==stock
        assert result['old_after']['bdf']=='0000:37:04.1' and result['old_after']['driver'] is None
        assert 'done=1 status=0 residual=0 selector=9 length=1048576 released=0 guard_changes=0'==status
    print(attempt,'paired post-reset complete firmware reads verified:',reqs[0]['boot_id'])

accepted=root/'accepted'
result=json.loads((accepted/'result.json').read_text())
reads=json.loads(gzip.decompress((accepted/'persist/engine-reads.json.gz').read_bytes()))
assert len(reads)==result['engine_wad_reads']==5043
for i,row in enumerate(reads):
    assert (row['offset'],row['n'])==struct.unpack_from('<II',oracle,8*i),i
    assert row['request_seq']==42+i
frame=(accepted/'persist/game-frame.bin').read_bytes()
assert len(frame)==65536
assert hashlib.sha256(frame).hexdigest()==result['game_frame_sha256']==\
    'f4d1c27a4ec8e8db4437d9e28012107370749765aa0e09c99758eeb54163b8ce'
assert (accepted/'persist/game-frame.pgm').read_bytes()==b'P5\n320 200\n255\n'+frame[:64000]
assert len(set(frame[:64000]))>32
er=[int(x,16) for x in result['engine_report']]
eng=[int(x,16) for x in result['engine_results']]
claim=[int(x,16) for x in result['claim_report']]
bank=[int(x,16) for x in result['bank_report']]
assert er[0:2]==[0x314d5246,2] and er[4:6]==[0x454e4702,1]
assert er[9:11]==[0,1] and er[11]==er[12]
assert eng[0:3]==[0x454e4750,2,6291456] and eng[5]==1 and eng[9:12]==[2,1,210]
assert bank[1]==bank[8]==bank[10]==bank[12]==bank[13]==0 and bank[2]==bank[7]==bank[9]==2048
assert claim[5:7]==[0x45495551,0] and result['old']['driver'] is None
assert result['wad_good']==5081 and result['wad_bad']==4 and result['upload_bytes']==867792
assert result['heartbeat_after']>result['heartbeat_before'] and result['release']=='reboot-only'
print('accepted run: native WAD trace, frame bytes, arena, bank and quiescent owner verified')
