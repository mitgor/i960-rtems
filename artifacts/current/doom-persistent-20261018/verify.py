#!/usr/bin/env python3
"""Replay the persistent card acceptance, including every captured DMA frame."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import tarfile
import tempfile
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
STOCK='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
sha=lambda b:hashlib.sha256(b).hexdigest()


def fnv(data):
    h=2166136261
    for b in data:h=((h^b)*16777619)&0xffffffff
    return h


def check_frame(row,blob):
    n=row['generation']
    assert row['slot']==(n-1)&1
    assert len(blob)==77824 and blob[:4096]==b'\xa5'*4096
    assert blob[69664:]==b'\xa5'*8160
    marker=struct.unpack_from('<8I',blob,69632)
    assert marker==(0x31505044,0x161610e1,n,row['slot'],65536,row['source'],row['card_tick'],(~n)&0xffffffff)
    image=blob[4096:69632]
    assert sha(image)==row['sha256'] and fnv(image)==int(row['fnv'],16)
    return image


def check(root,wad):
    session,=list((root/'sessions').iterdir());run=session/'run'
    r=json.loads((run/'result.json').read_text())
    assert r['persistent'] and r['frames']>1024 and r['frames']==r['dma_frames']
    assert r['stop_reason']=='browser STOP' and r['key_sequence_sent']==r['key_sequence_acked']>=4
    assert r['old']['driver'] is None and r['release']=='reboot-only' and r['full_audits_before']
    for n in (0,1):
        p=session/f'pre-{n}'
        assert sha((p/'data.bin').read_bytes())==STOCK
        state=dict(x.split('=') for x in (p/'status.txt').read_text().split())
        assert all(state[k]=='0' for k in ('status','residual','guard_changes'))
    page=(run/'persist/quiescent-page.bin').read_bytes()
    assert struct.unpack_from('<3I',page,0xb54)==(0x45495551,0,0xc0810010)
    er=struct.unpack_from('<16I',page,0xc40)
    assert er[0:2]==(0x314d5246,2) and er[9:11]==(0,1) and er[11]==er[12]
    results=struct.unpack_from('<12I',page,0xc80)
    assert results[9:]==(2,1,210) and results[5] in (r['frames'],r['frames']+1)
    rows=[json.loads(x) for x in (run/'persist/live-frame-receipts.jsonl').read_text().splitlines()]
    assert len(rows)==r['frames']
    for n,row in enumerate(rows,1):
        assert row['generation']==n
        blob=(run/f'persist/dma-frame-{n:04d}.bin').read_bytes()
        image=check_frame(row,blob)
        assert image==(run/f'persist/live-frames/frame-{n:04d}.bin').read_bytes()
    first=(run/'persist/dma-frame-0001.bin').read_bytes()
    for index in (0,4096,69632,77823):
        changed=bytearray(first);changed[index]^=1
        try:check_frame(rows[0],changed)
        except AssertionError:pass
        else:raise AssertionError('tampered capture accepted')
    baseline=ROOT/'artifacts/current/wide-screen-copy-20261018/first.tar.xz'
    with tarfile.open(baseline) as t:
        for n in range(1,33):
            ref=t.extractfile(f'case/run/persist/live-frames/frame-{n:04d}.bin').read()
            now=(run/f'persist/live-frames/frame-{n:04d}.bin').read_bytes()
            assert ref[:64768]==now[:64768], f'accepted Doom pixel/palette baseline frame {n}'
    assert sha((run/'persist/game-frame.bin').read_bytes())==rows[-1]['sha256']==r['game_frame_sha256']
    reads=[json.loads(x) for x in (run/'persist/engine-reads.jsonl').read_text().splitlines()]
    oracle=list(struct.iter_unpack('<II',(root/'bundle/inputs/native-requests.bin').read_bytes()))
    assert [(x['offset'],x['n']) for x in reads[:len(oracle)]]==oracle
    assert len(reads)==r['engine_wad_reads']
    for row in reads:
        block=wad[row['offset']:row['offset']+row['n']]
        assert len(block)==row['n'] and sha(block)==row['source_sha256'] and fnv(block)==int(row['source_fnv'],16)
    http=json.loads((HERE/'http/result.json').read_text())
    for row in http['frames']:assert rows[row['generation']-1]['sha256']==row['sha256']
    assert http['stop_posted'] and len(http['events'])==4
    return dict(frames=len(rows),http_frames=len(http['frames']),key_events=r['key_sequence_acked'],
                native_wad_reads=len(reads),oracle_reads=len(oracle),
                engine_startup_seconds=(rows[0]['card_tick']-er[2])/100,
                fixed_window_12_31_card_fps=1900/(rows[30]['card_tick']-rows[11]['card_tick']),
                last_64_card_fps=r['frame_timing']['render_fps'],
                all_frame_guards_hashes_markers=True,final_frame_exact=True,
                tamper_rejections=4,first_32_pixels_palette_match_accepted=True,
                engine_cleanup_and_quiescent_stop=True,old_card_unbound=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,default=HERE/'acceptance-pre-reset.tar.xz')
    a=p.parse_args()
    with zipfile.ZipFile(ROOT/'artifacts/doom-m1-20261011/freedoom-0.13.0.zip') as z:
        name,=[n for n in z.namelist() if n.endswith('/freedoom1.wad')];wad=z.read(name)
    assert sha(wad)=='7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d'
    with tempfile.TemporaryDirectory(prefix='i960-persistent-replay-') as tmp:
        root=Path(tmp)
        with tarfile.open(a.archive) as t:t.extractall(root,filter='data')
        report=check(root,wad)
    if (HERE/'post-0').exists():
        post_boots=[]
        for n in (0,1):
            p=HERE/f'post-{n}';assert sha((p/'data.bin').read_bytes())==STOCK
            request=json.loads((p/'request.json').read_text())
            result=json.loads((p/'result.json').read_text())
            assert result['old_after']['driver'] is None and result['bytes']==1048576
            post_boots.append(request['boot_id'])
            state=dict(x.split('=') for x in (p/'status.txt').read_text().split())
            assert all(state[k]=='0' for k in ('status','residual','guard_changes'))
        assert post_boots[0]==post_boots[1]
        report['paired_post_reset_flash_reads']=True
    else:report['paired_post_reset_flash_reads']=False
    fresh=HERE/'fresh-session.tar.xz'
    if fresh.exists():
        with tempfile.TemporaryDirectory(prefix='i960-persistent-fresh-') as tmp:
            root=Path(tmp)
            with tarfile.open(fresh) as t:t.extractall(root,filter='data')
            session,=list((root/'sessions').iterdir());run=session/'run'
            r=json.loads((run/'result.json').read_text())
            rows=[json.loads(x) for x in (run/'persist/live-frame-receipts.jsonl').read_text().splitlines()]
            assert r['frames']==r['dma_frames']==len(rows)==1565
            assert r['stop_reason']=='engine quit' and r['old']['driver'] is None
            assert [x['generation'] for x in rows]==list(range(1,len(rows)+1))
            samples=list((run/'persist').glob('dma-frame-*.bin'))
            for p in samples:
                n=int(p.stem.rsplit('-',1)[1]);check_frame(rows[n-1],p.read_bytes())
            assert sha((run/'persist/game-frame.bin').read_bytes())==rows[-1]['sha256']
            page=(run/'persist/quiescent-page.bin').read_bytes()
            assert struct.unpack_from('<2I',page,0xb54)==(0x45495551,0)
            er=struct.unpack_from('<16I',page,0xc40)
            assert er[9:11]==(0,1) and er[11]==er[12]
            assert struct.unpack_from('<3I',page,0xd28)==(98,121,97)
            report['fresh_session']=dict(frames=len(rows),captured_dma_samples=len(samples),
                final_frame_exact=True,quiescent_engine_quit=True,post_reset_pair_pending=True)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
