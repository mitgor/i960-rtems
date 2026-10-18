#!/usr/bin/env python3
"""Replay final NMI recovery and one normal game; this is a live idle snapshot."""
import hashlib,json,struct,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def fnv(b):
    h=2166136261
    for v in b:h=((h^v)*16777619)&0xffffffff
    return h
with tarfile.open(HERE/'mode0-restored-live.tar.xz') as t:
    files={m.name:t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
def read(n):return files[n]
def js(n):return json.loads(read(n))
def rows(n):return [json.loads(x) for x in read(n).splitlines()]
for name,digest in js('bundle/bundle.json')['files'].items():
    assert sha(read('bundle/'+name))==digest,name
manifest=js('bundle/project/rtems/accele160/doom_dma/persistent-manifest.json')
assert manifest['terminal_test']==0 and manifest['service_schema']==1
assert sha(read('bundle/kernel/kernel.bin'))==manifest['kernel_sha256']=='4a9c0278ff23815ea94d546a7fc43bfc3566c8ff916b70d0c2b0e7e42582ad3e'
run,={n[:-len('/games.json')] for n in files if n.endswith('/run/games.json')}
session=run[:-4];boots=[]
for i in (0,1):
    base=session+f'/pre-{i}'
    assert sha(read(base+'/data.bin'))=='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd'
    status=dict(x.split('=') for x in read(base+'/status.txt').decode().split())
    assert status['done']=='1' and all(status[k]=='0' for k in ('status','residual','guard_changes'))
    boots.append(js(base+'/request.json')['boot_id'])
assert boots[0]==boots[1]=='aea81f51-24ce-493b-a7d2-114195611d5b'
game,=js(run+'/games.json');assert game['frames']==64 and game['idle_verified']
d=run+'/persist/game-0001';frames=rows(d+'/live-frame-receipts.jsonl');assert len(frames)==64
for n,r in enumerate(frames,1):
    assert r['generation']==r['local_frame']==n and r['game_run']==1
    b=read(d+f'/dma-frame-{n:04d}.bin');assert len(b)==77824
    assert b[:4096]==b'\xa5'*4096 and b[69664:]==b'\xa5'*8160
    assert struct.unpack_from('<8I',b,69632)==(0x31505044,0x161610e1,n,(n-1)&1,65536,r['source'],r['card_tick'],(~n)&0xffffffff)
    image=b[4096:69632];assert sha(image)==r['sha256'] and fnv(image)==int(r['fnv'],16)
    assert image==read(d+f'/live-frames/frame-{n:04d}.bin')
    if n<=32:assert r['paired_pio']
wad=read('bundle/inputs/freedoom1.wad');reads=rows(d+'/engine-reads.jsonl')
assert len(reads)==game['wad_reads']
oracle=list(struct.iter_unpack('<II',read('bundle/inputs/native-requests.bin')))
assert [(r['offset'],r['n']) for r in reads[:len(oracle)]]==oracle
for r in reads:
    b=wad[r['offset']:r['offset']+r['n']];assert sha(b)==r['source_sha256'] and fnv(b)==int(r['source_fnv'],16)
idle=read(d+'/idle-verified.bin');b=struct.unpack_from('<32I',idle,0xb80)
assert b[17]==b[20]==b[21]==1 and b[25]==b[26] and not b[27]&1
v=struct.unpack_from('<32I',idle,0xd80);assert v[:3]==(0x31464d44,0x161610e1,0) and v[11]==64 and v[14:16]==(0,0)
journal=rows(run+'/console.jsonl');lat=[]
assert not any(r['event'] in ('quarantine','timeout') for r in journal)
for r in journal:
    if r['event'] not in ('reply','selftest'):continue
    wire=bytes.fromhex(r['wire']);w=struct.unpack_from('<32I',wire)
    assert len(wire)==896 and w[16]==r['seq'] and w[24]==0x31435653 and 0<w[19]<=768
    assert w[17]==r.get('expected',r.get('status'))
    text=wire[128:128+w[19]].decode('ascii')
    if w[17]:assert text==f'error={w[17]}\n'
    if r['event']=='reply':
        assert not w[17] and w[18]==r['epoch'] and text==r['text'];lat.append(r['latency_ms'])
assert sum(r['event']=='selftest_pass' for r in journal)==2 # startup plus one game idle
assert sum(r['event']=='idle_gate' for r in journal)==1
clients=js('restored-console.json');assert len(clients)>20 and not any('error' in r for r in clients)
assert {r['command'] for r in clients[:7]}=={'help','version','uptime','tasks','mem','apps','stats'}
assert clients[7]['text']=='error: unknown command\n' and clients[8]['text']=='error: command too long\n'
assert all('error:' not in r['text'] for r in clients[9:])
print(json.dumps(dict(boot_id=boots[0],nmi_reset_recovery_verified=True,normal_kernel=manifest['kernel_sha256'],
    frames=64,paired_pio_frames=32,wad_reads=len(reads),idle_verified=True,console_replies=len(lat),
    external_exchanges=len(clients),external_errors=0,max_console_latency_ms=max(lat),
    session_left_running=True,global_stop_tested=False,owned_exception_runtime=False),indent=2))
