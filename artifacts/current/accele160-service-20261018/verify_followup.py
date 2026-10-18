#!/usr/bin/env python3
"""Replay the corrected host's live-idle snapshot, not a global shutdown claim."""
import contextlib,io,json,runpy,struct,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
with contextlib.redirect_stdout(io.StringIO()):
    base=runpy.run_path(str(HERE/'verify.py'))
sha,fnv,frame,console,wad=(base[k] for k in ('sha','fnv','frame','console','wad'))
with tarfile.open(HERE/'followup.tar.xz') as t:
    def read(n):return t.extractfile(n).read()
    def js(n):return json.loads(read(n))
    def lines(n):return [json.loads(x) for x in read(n).splitlines()]
    names=set(t.getnames());verified=0
    for name,digest in js('bundle/bundle.json')['files'].items():
        if 'bundle/'+name in names:assert sha(read('bundle/'+name))==digest,name;verified+=1
        else:assert name=='inputs/freedoom1.wad'
    assert sha(read('bundle/kernel/kernel.bin'))==base['report']['kernel_sha256']
    run,={n[:-len('/games.json')] for n in names if n.endswith('/run/games.json')}
    games=js(run+'/games.json');assert len(games)==1
    g=games[0];assert g['idle_verified'] and g['frames']==64 and g['reason']=='frame limit'
    d=run+'/persist/game-0001';rows=lines(d+'/live-frame-receipts.jsonl')
    assert len(rows)==64;pio=0
    for n,row in enumerate(rows,1):
        assert row['generation']==row['local_frame']==n and row['game_run']==1
        image=frame(row,read(d+f'/dma-frame-{n:04d}.bin'))
        assert image[:64768]==base['frames_first'][n-1]
        assert image==read(d+f'/live-frames/frame-{n:04d}.bin')
        if n<=32:assert row['paired_pio'];pio+=1
    reads=lines(d+'/engine-reads.jsonl');assert len(reads)==g['wad_reads']
    oracle=list(struct.iter_unpack('<II',read('bundle/inputs/native-requests.bin')))
    assert [(r['offset'],r['n']) for r in reads[:len(oracle)]]==oracle
    for r in reads:
        block=wad[r['offset']:r['offset']+r['n']]
        assert sha(block)==r['source_sha256'] and fnv(block)==int(r['source_fnv'],16)
    idle=read(d+'/idle-verified.bin');b=struct.unpack_from('<32I',idle,0xb80)
    assert b[17]==b[20]==b[21]==1 and b[25]==b[26] and not b[27]&1
    dma=struct.unpack_from('<32I',idle,0xd80)
    assert dma[:3]==(0x31464d44,0x161610e1,0) and dma[11]==64 and dma[14:16]==(0,0)
    er=struct.unpack_from('<16I',idle,0xc40);assert er[9:11]==(0,1) and er[11]==er[12]
    journal=lines(run+'/console.jsonl');lat=[]
    assert not any(r['event'] in ('quarantine','timeout') for r in journal)
    for r in journal:
        if r['event'] in ('reply','selftest'):console(r)
        if r['event']=='reply':assert r['status']==0;lat.append(r['latency_ms'])
    assert sum(r['event']=='selftest_pass' for r in journal)==2
    assert sum(r['event']=='idle_gate' for r in journal)==1
    clients=js('followup-client.json');assert len(clients)>100
    assert not any('error' in r for r in clients)
    assert {r['command'] for r in clients[:7]}=={'help','version','uptime','tasks','mem','apps','stats'}
    assert clients[7]['command']=='unknown' and 'error:' in clients[7]['text']
    assert len(clients[8]['command'])==129 and 'error:' in clients[8]['text']
    assert all('error:' not in r['text'] for r in clients[9:])
    print(json.dumps(dict(bundle_files_verified=verified,kernel_sha256=base['report']['kernel_sha256'],
        frames=64,paired_pio_frames=pio,wad_reads_replayed=len(reads),idle_verified=True,
        console_replies=len(lat),console_selftest_gates=2,external_exchanges=len(clients),
        external_errors=0,oversized_line_clean_eof=True,
        console_latency_ms=dict(min=min(lat),median=sorted(lat)[len(lat)//2],max=max(lat)),
        global_stop=False,session_left_running=True),indent=2))
