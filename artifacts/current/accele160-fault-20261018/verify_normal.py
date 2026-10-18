#!/usr/bin/env python3
"""Replay normal-profile app/rearm/console evidence; live idle is not global STOP."""
import contextlib,io,json,runpy,struct,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
with contextlib.redirect_stdout(io.StringIO()):
    base=runpy.run_path(str(HERE.parent/'accele160-service-20261018/verify.py'))
sha,fnv,frame,console,wad=(base[k] for k in ('sha','fnv','frame','console','wad'))
with tarfile.open(HERE/'mode0-live.tar.xz') as t:
    def read(n):return t.extractfile(n).read()
    def js(n):return json.loads(read(n))
    def lines(n):return [json.loads(x) for x in read(n).splitlines()]
    names=set(t.getnames());verified=0
    for name,digest in js('bundle/bundle.json')['files'].items():
        if 'bundle/'+name in names:assert sha(read('bundle/'+name))==digest,name;verified+=1
        else:assert name=='inputs/freedoom1.wad'
    m=js('bundle/project/rtems/accele160/doom_dma/persistent-manifest.json')
    assert m['terminal_schema']==1 and m['terminal_test']==0 and m['service_schema']==1
    assert sha(read('bundle/kernel/kernel.bin'))==m['kernel_sha256']
    with tarfile.open(HERE/'mode0-prepared.tar.xz') as prepared:
        assert read('bundle/kernel/kernel.bin')==prepared.extractfile('bundle/kernel/kernel.bin').read()
    run,={n[:-len('/games.json')] for n in names if n.endswith('/run/games.json')}
    games=js(run+'/games.json');assert len(games)==2
    count=0;pio=0;reads_total=0
    oracle=list(struct.iter_unpack('<II',read('bundle/inputs/native-requests.bin')))
    for game,g in enumerate(games,1):
        assert g['idle_verified'] and g['frames']==64 and g['reason']=='frame limit'
        d=run+f'/persist/game-{game:04d}';rows=lines(d+'/live-frame-receipts.jsonl');assert len(rows)==64
        for local,row in enumerate(rows,1):
            n=count+local
            assert row['generation']==n and row['local_frame']==local and row['game_run']==game
            image=frame(row,read(d+f'/dma-frame-{n:04d}.bin'))
            assert image[:64768]==base['frames_first'][local-1]
            assert image==read(d+f'/live-frames/frame-{n:04d}.bin')
            if local<=32:assert row['paired_pio'];pio+=1
        reads=lines(d+'/engine-reads.jsonl');assert len(reads)==g['wad_reads'];reads_total+=len(reads)
        assert [(r['offset'],r['n']) for r in reads[:len(oracle)]]==oracle
        for r in reads:
            block=wad[r['offset']:r['offset']+r['n']]
            assert sha(block)==r['source_sha256'] and fnv(block)==int(r['source_fnv'],16)
        idle=read(d+'/idle-verified.bin');b=struct.unpack_from('<32I',idle,0xb80)
        assert b[17]==b[21]==1 and b[20]==game and b[25]==b[26] and not b[27]&1
        dma=struct.unpack_from('<32I',idle,0xd80)
        assert dma[:3]==(0x31464d44,0x161610e1,0) and dma[11]==count+64 and dma[14:16]==(0,0)
        er=struct.unpack_from('<16I',idle,0xc40);assert er[9:11]==(0,1) and er[11]==er[12]
        count+=64
    journal=lines(run+'/console.jsonl');lat=[]
    assert not any(r['event'] in ('quarantine','timeout') for r in journal)
    for r in journal:
        if r['event'] in ('reply','selftest'):console(r)
        if r['event']=='reply':assert r['status']==0;lat.append(r['latency_ms'])
    assert sum(r['event']=='selftest_pass' for r in journal)==3
    assert sum(r['event']=='idle_gate' for r in journal)==2
    clients=js('mode0-client.json');assert len(clients)>100
    assert not any('error' in r for r in clients)
    assert {r['command'] for r in clients[:7]}=={'help','version','uptime','tasks','mem','apps','stats'}
    assert clients[7]['command']=='unknown' and 'error:' in clients[7]['text']
    assert len(clients[8]['command'])==129 and 'error:' in clients[8]['text']
    assert all('error:' not in r['text'] for r in clients[9:])
    boots=[]
    for i in (0,1):
        d=run.rsplit('/run',1)[0]+f'/pre-{i}'
        assert sha(read(d+'/data.bin'))==base['STOCK']
        status=dict(x.split('=') for x in read(d+'/status.txt').decode().split())
        assert all(status[k]=='0' for k in ('status','residual','guard_changes'))
        boots.append(js(d+'/request.json')['boot_id'])
    assert boots[0]==boots[1] and boots[0]!='03bd813b-ac1c-4925-9270-34e1f0a1fad8'
    print(json.dumps(dict(boot_id=boots[0],bundle_files_verified=verified,kernel_sha256=m['kernel_sha256'],
        frames=count,paired_pio_frames=pio,wad_reads_replayed=reads_total,idle_verified=True,
        console_replies=len(lat),console_selftest_gates=3,external_exchanges=len(clients),
        external_errors=0,oversized_line_clean_eof=True,mode2_post_reset_flash_pair=True,
        console_latency_ms=dict(min=min(lat),median=sorted(lat)[len(lat)//2],max=max(lat)),
        global_stop=False,session_left_running=True),indent=2))
