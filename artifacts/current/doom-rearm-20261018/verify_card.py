#!/usr/bin/env python3
"""Replay every frame/WAD read and rearm gate in the three-game card capture."""
import argparse,hashlib,json,struct,tarfile,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
STOCK='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
sha=lambda b:hashlib.sha256(b).hexdigest()
def fnv(b):
    h=2166136261
    for x in b:h=((h^x)*16777619)&0xffffffff
    return h
def check_frame(row,b):
    n=row['generation'];slot=row['slot']
    assert slot==(row['local_frame']-1)&1
    assert len(b)==77824 and b[:4096]==b'\xa5'*4096 and b[69664:]==b'\xa5'*8160
    assert struct.unpack_from('<8I',b,69632)==(0x31505044,0x161610e1,n,slot,65536,row['source'],row['card_tick'],(~n)&0xffffffff)
    image=b[4096:69632]
    assert sha(image)==row['sha256'] and fnv(image)==int(row['fnv'],16)
    return image
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--archive',type=Path,default=HERE/'card-acceptance-pre-reset.tar.xz');a=p.parse_args()
with zipfile.ZipFile(ROOT/'artifacts/doom-m1-20261011/freedoom-0.13.0.zip') as z:
    name,=[n for n in z.namelist() if n.endswith('/freedoom1.wad')];wad=z.read(name)
assert sha(wad)=='7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d'
with tarfile.open(a.archive) as t,tarfile.open(ROOT/'artifacts/current/wide-screen-copy-20261018/first.tar.xz') as baseline:
    def read(n):return t.extractfile(n).read()
    def js(n):return json.loads(read(n))
    def lines(n):return [json.loads(x) for x in read(n).splitlines()]
    session,={n.split('/run/')[0] for n in t.getnames() if n.endswith('/run/result.json')}
    run=session+'/run';r=js(run+'/result.json')
    assert r['reusable'] and r['persistent'] and r['old']['driver'] is None
    assert r['card']['bdf']=='0000:37:09.1' and r['card']['ids']==[4201,80,4201,84]
    manifest=json.loads((HERE/'status.json').read_text())['manifest']
    assert r['kernel_sha256']==manifest['kernel_sha256'] and r['image_sha256']==manifest['image_sha256']
    inventory=js('bundle-retry/bundle.json')
    host_source='project/rtems/accele160/doom_dma/run_bridge.py'
    assert sha(read('bundle-retry/'+host_source))==inventory['files'][host_source]
    with tarfile.open(HERE/'candidate.tar.xz') as frozen:
        engine_bytes=frozen.extractfile('bundle-candidate/engine/manifest.json').read()
        assert sha(engine_bytes)==manifest['engine_manifest_sha256']
        engine=json.loads(engine_bytes)
    assert len(r['games'])==3 and r['frames']==r['dma_frames']==sum(g['frames'] for g in r['games'])
    assert r['boot_id']!='31291627-dcd0-44bd-9c81-50708c818d80'
    for i in (0,1):
        d=session+f'/pre-{i}'
        assert sha(read(d+'/data.bin'))==STOCK
        request=js(d+'/request.json');assert request['boot_id']==r['boot_id']
        s=dict(x.split('=') for x in read(d+'/status.txt').decode().split())
        assert all(s[k]=='0' for k in ('status','residual','guard_changes'))
    oracle=list(struct.iter_unpack('<II',read('bundle-candidate/inputs/native-requests.bin')))
    ready=read(run+'/persist/ready-page.bin');claim0=struct.unpack_from('<16I',ready,0xb40)
    allrows=[];last_wad=None;reports=[];discarded=[]
    for game in (1,2,3):
        d=run+f'/persist/game-{game:04d}';g=js(d+'/game-result.json');assert g['game_run']==game and g['idle_verified']
        assert g['reason']==('menu Quit' if game==2 else 'frame limit')
        rows=lines(d+'/live-frame-receipts.jsonl');assert len(rows)==g['frames']
        for local,row in enumerate(rows,1):
            n=len(allrows)+local
            assert row['generation']==n and row['local_frame']==local and row['game_run']==game
            assert row['source']==claim0[7]+engine['play_offset']+row['slot']*65536
            assert row['card_fnv_mode']=='off' and int(row['card_fnv'],16)==0
            image=check_frame(row,read(d+f'/dma-frame-{n:04d}.bin'))
            assert image==read(d+f'/live-frames/frame-{n:04d}.bin')
            if local<=32:
                ref=baseline.extractfile(f'case/run/persist/live-frames/frame-{local:04d}.bin').read()
                assert image[:64768]==ref[:64768],f'game {game} baseline frame {local}'
                assert row['paired_pio']
        assert sha(read(d+'/game-frame.bin'))==rows[-1]['sha256']==g['frame_sha256']
        if game==1:
            sample=read(d+'/dma-frame-0001.bin')
            for index in (0,4096,69632,77823):
                changed=bytearray(sample);changed[index]^=1
                try:check_frame(rows[0],changed)
                except AssertionError:pass
                else:raise AssertionError('tampered capture accepted')
        reads=lines(d+'/engine-reads.jsonl');assert len(reads)==g['wad_reads']
        assert [(x['offset'],x['n']) for x in reads[:len(oracle)]]==oracle
        for row in reads:
            if last_wad is not None:assert row['request_seq']==last_wad+1
            last_wad=row['request_seq'];block=wad[row['offset']:row['offset']+row['n']]
            assert sha(block)==row['source_sha256'] and fnv(block)==int(row['source_fnv'],16)
        idle=read(d+'/idle-verified.bin');c=struct.unpack_from('<16I',idle,0xb40)
        assert c[:4]==claim0[:4] and c[7:]==claim0[7:] and c[6]==0
        b=struct.unpack_from('<32I',idle,0xb80);dma=struct.unpack_from('<32I',idle,0xd80)
        assert b[17]==1 and b[20]==game and b[21]==1 and b[22]==len(allrows)+len(rows)
        assert b[25]==b[26] and not b[27]&1
        assert dma[:3]==(0x31464d44,0x161610e1,0) and dma[11]==b[22] and dma[14:16]==(0,0)
        er=struct.unpack_from('<16I',idle,0xc40);assert er[9:11]==(0,1) and er[11]==er[12]
        if game<3:
            rearm=js(d+'/rearm.json');assert rearm['next_run']==game+1;discarded.append(rearm['discarded_key'])
        reports.append(dict(game=game,frames=len(rows),wad_reads=len(reads),reason=g['reason'],
            first_generation=rows[0]['generation'],last_generation=rows[-1]['generation'],
            startup_s=(rows[0]['card_tick']-er[2])/100,elapsed_s=g['elapsed_s']))
        allrows.extend(rows)
    receipts=js(run+'/persist/bridge-receipts.json')
    assert sum(x['op']==8 and x['status']==0 for x in receipts)==2
    for code in (40,42,43,44,45):assert sum(x['op']==8 and x['status']==code for x in receipts)==3
    assert sum(x['op']==7 and x['status']==20 for x in receipts)==3
    final=read(run+'/persist/quiescent-page.bin')
    assert struct.unpack_from('<2I',final,0xb54)==(0x45495551,0)
    assert struct.unpack_from('<I',final,0xa54)[0]==0x214b4341
    assert final[0xb00:0xb40]==ready[0xb00:0xb40]
    assert sum(g['wad_reads'] for g in reports)+38==r['wad_good'] and r['wad_bad']==4
    http=js('http-observations.json') if 'http-observations.json' in t.getnames() else json.loads((HERE/'http/observations.json').read_text())
    for x in http['frames']:assert x['sha256']==allrows[x['generation']-1]['sha256']
    report=dict(boot_id=r['boot_id'],games=reports,total_frames=len(allrows),http_samples=len(http['frames']),
        first_32_pixels_palette_exact_each_game=True,all_wad_requests_replayed=True,
        full_dma_guards_markers_hashes=True,paired_pio_frames=96,
        successful_rearms=2,stale_rearm_rejections=15,retired_entry_rejections=3,
        discarded_old_game_keys=discarded,global_generation_differs_from_local_slot_parity=any(x['slot']!=((x['generation']-1)&1) for x in allrows),
        final_global_quiescence=True,old_card_unbound=True,post_reset_flash_pair=False)
    reports_post=[]
    if (HERE/'post-0/result.json').exists() and (HERE/'post-1/result.json').exists():
        for number in (0,1):
            d=HERE/f'post-{number}'
            assert sha((d/'data.bin').read_bytes())==STOCK
            request=json.loads((d/'request.json').read_text())
            result=json.loads((d/'result.json').read_text())
            state=dict(x.split('=') for x in (d/'status.txt').read_text().split())
            assert all(state[k]=='0' for k in ('status','residual','guard_changes'))
            assert request['boot_id']!=r['boot_id'] and result['bytes']==1048576
            assert result['card_after']['bdf']=='0000:37:09.1' and result['card_after']['ids']==[4201,80,4201,84]
            assert result['old_after']['driver'] is None
            reports_post.append(request['boot_id'])
        assert reports_post[0]==reports_post[1]
        report['post_reset_flash_pair']=True;report['post_reset_boot_id']=reports_post[0]
        report['post_reset_old_card_absent']=json.loads((HERE/'post-1/result.json').read_text())['old_after'].get('present') is False
    print(json.dumps(report,indent=2))
