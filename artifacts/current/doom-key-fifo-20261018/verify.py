#!/usr/bin/env python3
"""Replay bounded FIFO acceptance, source identities and received-frame timing.

Reads archives as data; executes no archived program. A missing post-reset pair
is reported explicitly. Paired PIO comparisons were done by the owning bridge.
"""
import hashlib
import json
from pathlib import Path
import statistics
import struct
import sys
import tarfile
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'rtems/accele160/doom_dma'))
import key_fifo

def sha(b):return hashlib.sha256(b).hexdigest()
def check(ok,message):
    if not ok:raise ValueError(message)
def archive(path):
    with tarfile.open(path) as t:
        return {m.name:t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
def js(data):return json.loads(data)
def lines(data):return [js(line) for line in data.splitlines()]
def fnv(data):
    h=2166136261
    for byte in data:h=((h^byte)*16777619)&0xffffffff
    return h
def measured(runs):
    result={}
    for burst in sorted({p['burst'] for r in runs for p in r['probes']}):
        modes={}
        for mode in ('mailbox','fifo'):
            probes=[p for r in runs if r['mode']==mode for p in r['probes'] if p['burst']==burst]
            values=[t['ms'] for p in probes for t in p['trials']]
            modes[mode]=dict(n=len(values),median_ms=statistics.median(values),
                min_ms=min(values),max_ms=max(values),mean_delivered_fps=statistics.mean(p['delivered_fps'] for p in probes))
        modes['reduction_percent']=(1-modes['fifo']['median_ms']/modes['mailbox']['median_ms'])*100
        result[str(burst)]=modes
    return result

card=archive(HERE/'card-evidence-final.tar.xz')
build=archive(HERE/'build-evidence.tar.xz')
baseline=archive(HERE.parent/'accele160-flat-20261018/acceptance-pre-reset.tar.xz')
result=js(card['run/result.json'])
check(result['frames']==result['dma_frames']==3073 and result['full_audits_before'],'global full audits/frame count')
check(result['grant_retained'] and result['release']=='reboot-only' and not result['old']['present'],'exclusive retained ownership')
manifest=js(build['bundle/bundle.json']);covered=0
for name,digest in manifest['files'].items():
    data=build.get('bundle/'+name)
    if data is None and name.startswith('kernel/'):data=build.get(name)
    if data is None:data=baseline.get('bundle/'+name)
    # WAD is retained once in the original upstream source archive.
    if data is None and name.endswith('freedoom1.wad'):
        with zipfile.ZipFile(ROOT/'artifacts/doom-m1-20261011/freedoom-0.13.0.zip') as z:
            member,=[n for n in z.namelist() if n.endswith('/freedoom1.wad')];data=z.read(member)
    check(data is not None and sha(data)==digest,'pinned bundle member: '+name);covered+=1
check(sha(build['kernel/kernel.bin'])==result['kernel_sha256'],'kernel identity')
check(sha(build['kernel/image.bin'])==result['image_sha256'],'kernel image identity')
check(js(build['kernel/build.json'])['keyboard_fifo_schema']==1,'FIFO build switch')
stock=result['firmware_sha256']
canonical=ROOT/'artifacts/current/accele160-preempt-20261017/live/after-accept1-flash-0/data.bin'
check(sha(canonical.read_bytes())==stock,'canonical firmware bytes')
for i in (0,1):
    prefix=f'pre-{i}/';s=dict(x.split('=') for x in card[prefix+'status.txt'].decode().split())
    check(all(s[k]=='0' for k in ('status','residual','guard_changes')),'pre flash DMA status')
    check(js(card[prefix+'result.json'])['sha256']==stock and js(card[prefix+'request.json'])['boot_id']==result['boot_id'],'pre flash identity')
with zipfile.ZipFile(ROOT/'artifacts/doom-m1-20261011/freedoom-0.13.0.zip') as z:
    member,=[n for n in z.namelist() if n.endswith('/freedoom1.wad')];wad=z.read(member)
native=list(struct.iter_unpack('<II',baseline['bundle/inputs/native-requests.bin']))
ready=card['run/persist/ready-page.bin'];claim=struct.unpack_from('<16I',ready,0xb40)
options=js(baseline['bundle/engine/manifest.json'])
reference_prefix,={n.split('/run/')[0] for n in baseline if n.endswith('/run/result.json')}
reference=f'{reference_prefix}/run/persist/game-0004/live-frames/'
references={i:baseline[reference+f'frame-{384+i:04d}.bin'] for i in range(1,33)}
receipts={};details=[];previous=None;last_request=None;read_cache={};native_matches=0;captures=0
games=js(card['run/games.json'])
check(len(games)==8,'eight fresh games')
for game in games:
    number=game['game_run'];prefix=f'run/persist/game-{number:04d}/'
    rows=lines(card[prefix+'live-frame-receipts.jsonl']);k=game['keyboard']
    check(len(rows)==game['frames'] and game['idle_verified'],'per-game full audits/idle')
    check(sum(r['paired_pio'] for r in rows)==32,'32 paired PIO comparisons per game')
    check(k['acked']==k['consumed']+k['discarded'] and k['published']==k['acked']+k['pending'],'consumption/discard conservation')
    check(k['max_depth']<=(16 if k['mode']=='fifo' else 1),'bounded per-game queue')
    page=card[prefix+'prestop-page.bin'];key_fifo.pending(page,k['published'],number,k['mode'])
    if previous:
        check(k['discarded']-previous['discarded']==previous['pending'],'no inherited old-game input')
    previous=k
    idle=card[prefix+'idle-verified.bin'];c=struct.unpack_from('<16I',idle,0xb40)
    b=struct.unpack_from('<32I',idle,0xb80);er=struct.unpack_from('<16I',idle,0xc40)
    check(c[:4]==claim[:4] and c[7:]==claim[7:] and c[6]==0 and b[17]==1 and b[25]==b[26] and not b[27]&1,'idle private allocation and IRQ gates')
    check(er[9:11]==(0,1) and er[11]==er[12],'idle heap drain')
    check(b'guard_changes=0' in card[prefix+'dma-pin-latest.txt'],'host DMA guards')
    start_pub=0 if number==1 else games[number-2]['keyboard']['published']
    submitted=0;ack=start_pub;published=start_pub
    for event in lines(card[prefix+'keyboard-receipts.jsonl']):
        if event['op']=='submit':
            check(0<len(event['events'])<=16 and all(0<=e<=511 for e in event['events']),'bounded key journal')
            submitted+=len(event['events']);published+=len(event['events'])
            check(event['last_seq']==published<=k['published'] and ack<=event['acked']<=published,'published sequence journal')
        elif event['op']=='ack':
            check(ack<event['seq']<=min(k['acked'],published) and 0<=event['card_frame']<=game['frames'],'ordered consumption journal');ack=event['seq']
        else:raise ValueError('unknown key journal entry')
    check(submitted==k['published']-start_pub,'all publications journalled')
    for local,row in enumerate(rows,1):
        check(row['local_frame']==local and row['game_run']==number and row['generation']==len(receipts)+1,'frame sequence')
        receipts[row['generation']]=row
        raw=card.get(prefix+f'live-frames/frame-{row["generation"]:04d}.bin')
        if raw is None:continue
        capture=card[prefix+f'dma-frame-{row["generation"]:04d}.bin'];source=claim[7]+options['play_offset']+row['slot']*65536
        check(len(capture)==77824 and capture[:4096]==b'\xa5'*4096 and capture[69664:]==b'\xa5'*8160,'capture DMA guards')
        check(row['slot']==(local-1)&1 and row['source']==source,'ping-pong ownership')
        check(struct.unpack_from('<8I',capture,69632)==(0x31505044,0x161610e1,row['generation'],row['slot'],65536,source,row['card_tick'],~row['generation']&0xffffffff),'DMA completion marker')
        check(capture[4096:69632]==raw and sha(raw)==row['sha256'] and fnv(raw)==int(row['fnv'],16),'capture exact hash')
        captures+=1
        if local<=32:
            check(raw[:64768]==references[local][:64768],'unchanged native-qualified baseline pixels/palette');native_matches+=1
    check(sha(card[prefix+'game-frame.bin'])==game['frame_sha256']==rows[-1]['sha256'],'final frame')
    reads=lines(card[prefix+'engine-reads.jsonl'])
    check(len(reads)==game['wad_reads'] and [(r['offset'],r['n']) for r in reads[:len(native)]]==native,'native startup request oracle')
    for r in reads:
        check(last_request is None or r['request_seq']==last_request+1,'WAD sequence');last_request=r['request_seq']
        identity=(r['offset'],r['n'])
        if identity not in read_cache:
            data=wad[r['offset']:r['offset']+r['n']];read_cache[identity]=(sha(data),fnv(data))
        check(read_cache[identity]==(r['source_sha256'],int(r['source_fnv'],16)),'WAD bytes/hash')
    details.append(dict(run=number,mode=k['mode'],frames=len(rows),paired_pio=32,keyboard=k,idle_verified=True))
check(games[0]['keyboard']['pending']==16 and games[-1]['keyboard']['discarded']==16,'full-ring STOP and committed retirement')
bridge=js(card['run/persist/bridge-receipts.json'])
check(sum(r['op']==8 and r['status']==0 for r in bridge)==7,'seven clean rearms')
for code in (40,42,43,44,45):check(sum(r['op']==8 and r['status']==code for r in bridge)==8,'stale identity rejection')
final=card['run/persist/quiescent-page.bin']
check(struct.unpack_from('<2I',final,0xb54)==(0x45495551,0) and final[0xb00:0xb40]==ready[0xb00:0xb40],'terminal QUIE/full-bank audit')
def source(generation,digest):check(generation in receipts and receipts[generation]['sha256']==digest,'observed audited frame source')
gateway=lines(card['transport.jsonl']);sent=[r for r in gateway if r['type']=='frame']
for r in sent:
    check(r['inflight']<=2,'bounded video credits');source(int(r['frame'].split('-')[1]),r['sha256'])
measurements={};observed=0
for folder in ('mac-abba','mac-single-abba'):
    runs=js((HERE/folder/'results.json').read_text());check([r['mode'] for r in runs]==['fifo','mailbox','mailbox','fifo'],'same-kernel ABBA order')
    for run in runs:
        check(run['initial']['flat_switches']==0,'no inherited F6 at fresh entry')
        for probe in run['probes']:
            for r in probe['frames']:source(r['generation'],r['sha256']);observed+=1
    measurements[folder]=measured(runs)
check(measurements==js((HERE/'comparison.json').read_text()),'reported comparison replay')
rejected=0
for generation,digest in ((-1,'0'*64),(1,'0'*64)):
    try:source(generation,digest)
    except ValueError:rejected+=1
    else:raise ValueError('tampered observer accepted')
sample=games[0];page=bytearray(card['run/persist/game-0001/prestop-page.bin'])
for offset in (key_fifo.OFFSET+80*4,key_fifo.OFFSET+(16+((145-1)&15)*4)*4,
               key_fifo.OFFSET+(17+((145-1)&15)*4)*4,key_fifo.OFFSET+7*4):
    changed=bytearray(page);changed[offset]^=1
    try:key_fifo.pending(changed,160,1,'fifo')
    except ValueError:rejected+=1
    else:raise ValueError('tampered pending FIFO accepted')
post=all((HERE/f'post-{i}/result.json').exists() for i in (0,1))
if post:
    boots=[]
    for i in (0,1):
        d=HERE/f'post-{i}';s=dict(x.split('=') for x in (d/'status.txt').read_text().split())
        check(all(s[k]=='0' for k in ('status','residual','guard_changes')),'post flash DMA guards')
        check(sha((d/'data.bin').read_bytes())==stock==js((d/'result.json').read_text())['sha256'],'post full flash identity')
        boots.append(js((d/'request.json').read_text())['boot_id'])
    check(boots[0]==boots[1] and boots[0]!=result['boot_id'],'post reset boot identity')
deployment=archive(HERE/'deployment.tar.xz')
gateway_manifest=js(deployment['gateway-manifest.json'])
wheel,=(HERE.parent/'doom-stream-20261018/dependencies').glob('*.whl')
with zipfile.ZipFile(wheel) as library:
    for name,digest in gateway_manifest.items():
        data=library.read(name[len('vendor/'):]) if name.startswith('vendor/') else deployment[name]
        check(sha(data)==digest,'installed gateway identity: '+name)
check(b'i960-key-fifo-20261018/bundle' in deployment['owner-launcher'],'default FIFO bundle')
production=archive(HERE/'production-smoke.tar.xz')
smoke=js((HERE/'production-smoke.json').read_text())
game=js(production['run/persist/game-0001/game-result.json'])
rows=lines(production['run/persist/game-0001/live-frame-receipts.jsonl'])
check(game['idle_verified'] and game['frames']==len(rows)==168 and sum(r['paired_pio'] for r in rows)==32,'ordinary launch full audits/PIO/STOP')
check(game['keyboard']['consumed']==game['keyboard']['published']==16 and game['keyboard']['pending']==0,'ordinary input conservation')
check(smoke['selftest_disabled'] and smoke['ordinary_start_and_stop'] and smoke['final']['state']=='idle','normal selftest disabled and reusable idle')
for row in smoke['probe']['frames']:
    check(rows[row['generation']-1]['sha256']==row['sha256'],'ordinary pushed frame source')
for row in rows[:32]:
    n=row['generation'];prefix='run/persist/game-0001/'
    capture=production[prefix+f'dma-frame-{n:04d}.bin'];raw=production[prefix+f'live-frames/frame-{n:04d}.bin']
    check(capture[:4096]==b'\xa5'*4096 and capture[69664:]==b'\xa5'*8160,'ordinary DMA guards')
    check(capture[4096:69632]==raw and sha(raw)==row['sha256'],'ordinary exact capture')
    check(raw[:64768]==references[n][:64768],'ordinary startup baseline pixels')
print(json.dumps(dict(games=details,frames=len(receipts),paired_pio_frames=256,retained_captures=captures,
    exact_baseline_frames=native_matches,native_oracle_reads_per_game=len(native),
    gateway_payloads=len(sent),client_frames=observed,bundle_members=covered,
    tamper_rejections=rejected,full_audits_and_ownership=True,post_reset_flash_pair=post,
    measurements=measurements,ordinary_launcher_smoke=dict(frames=168,paired_pio=32,
        default_fifo=True,selftest_disabled=True,reusable_idle=True,
        gateway_manifest_files=len(gateway_manifest))),indent=2))
