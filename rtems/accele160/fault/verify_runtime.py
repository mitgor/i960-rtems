#!/usr/bin/env python3
"""Replay an owned-runtime acceptance archive without running captured code."""
import argparse,hashlib,json,struct,tarfile
from host import validate_runtime
sha=lambda b:hashlib.sha256(b).hexdigest()
def fnv(b):
    h=2166136261
    for v in b:h=((h^v)*16777619)&0xffffffff
    return h

def verify(path,live=False):
    with tarfile.open(path) as t:
        files={m.name:t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
    def read(n):return files[n]
    def js(n):return json.loads(read(n))
    def rows(n):return [json.loads(x) for x in read(n).splitlines()]
    for name,h in js('bundle/bundle.json')['files'].items():assert sha(read('bundle/'+name))==h,name
    m=js('bundle/project/rtems/accele160/doom_dma/persistent-manifest.json')
    assert m['terminal_test'] in (5,14,15) and m['terminal_schema']==m['service_schema']==1
    assert sha(read('bundle/kernel/kernel.bin'))==m['kernel_sha256']
    assert sha(read('bundle/inputs/admit_command.ko'))==m['admit_module_sha256']
    run,={n[:-len('/games.json')] for n in files if n.endswith('/run/games.json')}
    session=run[:-4];boots=[]
    for i in (0,1):
        b=session+f'/pre-{i}'
        assert sha(read(b+'/data.bin'))=='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
        s=dict(x.split('=') for x in read(b+'/status.txt').decode().split())
        assert s['done']=='1' and all(s[k]=='0' for k in ('status','residual','guard_changes'))
        boots.append(js(b+'/request.json')['boot_id'])
    assert boots[0]==boots[1]
    symbols={a[2]:int(a[0],16) for line in read('bundle/kernel/kernel.symbols').decode().splitlines() if len(a:=line.split())==3}
    samples=js(run+'/owned-runtime.json');last_ticks=0;last_handoffs=0
    for r in samples:
        page=read(run+'/owned-'+r['label']+'.bin');nonce=struct.unpack_from('<I',page,68)[0]
        w=validate_runtime(page,nonce,r['sequence'],r['phase'],m['terminal_test'])
        if m['terminal_test'] in (14,15):
            import importlib.util
            spec=importlib.util.spec_from_file_location('engine_inventory',__import__('pathlib').Path(__file__).parent.parent/'ownership/inventory.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            module.decode(page,nonce,r['sequence'],r['phase'])
            if m['terminal_test']==15:
                spec=importlib.util.spec_from_file_location('qlogic_config',__import__('pathlib').Path(__file__).parent.parent/'ownership/qlogic_config.py')
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                module.decode(page,nonce,r['sequence'],r['phase'])
        assert w[148]==symbols['_accele_fault_entry'] and w[149]==symbols['_accele_nmi_entry']
        assert w[167]==r['ticks']>=last_ticks and w[168]==r['handoffs']>=last_handoffs
        last_ticks=w[167];last_handoffs=w[168]
    games=js(run+'/games.json');assert len(games)==(1 if live else 2)
    expected=['ready']
    for i in range(1,len(games)+1):expected += [f'game-{i}-frame32',f'game-{i}-idle']
    if not live:expected+=['quiescent']
    assert [r['label'] for r in samples]==expected
    assert last_ticks>samples[0]['ticks'] and last_handoffs>samples[0]['handoffs']
    wad=read('bundle/inputs/freedoom1.wad');count=0;wad_count=0
    oracle=list(struct.iter_unpack('<II',read('bundle/inputs/native-requests.bin')))
    for game,g in enumerate(games,1):
        assert g['frames']==64 and g['idle_verified']
        d=run+f'/persist/game-{game:04d}';fr=rows(d+'/live-frame-receipts.jsonl');assert len(fr)==64
        for local,r in enumerate(fr,1):
            n=count+local;assert r['generation']==n and r['local_frame']==local and r['game_run']==game
            b=read(d+f'/dma-frame-{n:04d}.bin');assert len(b)==77824
            assert b[:4096]==b'\xa5'*4096 and b[69664:]==b'\xa5'*8160
            assert struct.unpack_from('<8I',b,69632)==(0x31505044,0x161610e1,n,(local-1)&1,65536,r['source'],r['card_tick'],(~n)&0xffffffff)
            image=b[4096:69632];assert sha(image)==r['sha256'] and fnv(image)==int(r['fnv'],16)
            assert image==read(d+f'/live-frames/frame-{n:04d}.bin')
            if local<=32:assert r['paired_pio']
        rd=rows(d+'/engine-reads.jsonl');assert len(rd)==g['wad_reads'];wad_count+=len(rd)
        assert [(r['offset'],r['n']) for r in rd[:len(oracle)]]==oracle
        for r in rd:
            b=wad[r['offset']:r['offset']+r['n']];assert sha(b)==r['source_sha256'] and fnv(b)==int(r['source_fnv'],16)
        idle=read(d+'/idle-verified.bin');b=struct.unpack_from('<32I',idle,0xb80)
        assert b[17]==b[21]==1 and b[20]==game and b[25]==b[26] and not b[27]&1
        v=struct.unpack_from('<32I',idle,0xd80);assert v[:3]==(0x31464d44,0x161610e1,0) and v[11]==count+64 and v[14:16]==(0,0)
        count+=64
    journal=rows(run+'/console.jsonl');lat=[]
    assert not any(r['event'] in ('quarantine','timeout') for r in journal)
    for r in journal:
        if r['event'] not in ('reply','selftest'):continue
        raw=bytes.fromhex(r['wire']);w=struct.unpack_from('<32I',raw)
        assert len(raw)==896 and w[16]==r['seq'] and w[24]==0x31435653 and 0<w[19]<=768
        assert w[17]==r.get('expected',r.get('status'))
        text=raw[128:128+w[19]].decode('ascii')
        if w[17]:assert text==f'error={w[17]}\n'
        if r['event']=='reply':assert w[18]==r['epoch'] and text==r['text'] and not w[17];lat.append(r['latency_ms'])
    assert sum(r['event']=='selftest_pass' for r in journal)==len(games)+1
    if not live:
        q=read(run+'/persist/quiescent-page.bin')
        assert struct.unpack_from('<2I',q,0xb54)==(0x45495551,0)
        assert struct.unpack_from('<I',q,0xa54)[0]==0x214b4341
        assert 'done=0' in read(run+'/persist/admit-pending-status.txt').decode()
        assert 'guard_changes=0' in read(run+'/persist/dma-pin-final.txt').decode()
        assert samples[-1]['phase']==1
    clients=js('restored-console.json' if live else 'acceptance-console-corrected.json')
    assert len(clients)>20 and not any('error' in r for r in clients)
    assert {r['command'] for r in clients[:7]}=={'help','version','uptime','tasks','mem','apps','stats'}
    assert clients[7]['text']=='error: unknown command\n'
    assert clients[8]['text']=='error: command too long\n'
    assert all('error:' not in r['text'] for r in clients[9:])
    return dict(external_exchanges=len(clients),external_errors=0,boot_id=boots[0],kernel_sha256=m['kernel_sha256'],owned_samples=samples,
        frames=count,wad_reads=wad_count,console_replies=len(lat),max_console_latency_ms=max(lat),
        owned_vectors_and_guards=True,global_stop=not live,session_left_running=live)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('--live',action='store_true');a=p.parse_args()
    print(json.dumps(verify(a.archive,a.live),indent=2))
