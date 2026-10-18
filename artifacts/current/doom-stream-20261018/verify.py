#!/usr/bin/env python3
"""Replay transport identities against every original full-audit frame receipt.

Does not replace card audits or claim browser paint latency. Sources/dependency
are pinned independently; no executable from the evidence is run.
"""
import hashlib
import io
import json
from pathlib import Path
import statistics
import tarfile
import zipfile

root=Path(__file__).resolve().parent

def digest(data):return hashlib.sha256(data).hexdigest()

def check(condition, message):
    if not condition:raise ValueError(message)

def compare(receipt, generation, sha):
    check(generation in receipt and receipt[generation]['sha256']==sha,'frame source/hash mismatch')

receipts={}
with tarfile.open(root/'card-evidence-final.tar.xz') as card:
    def read(name):return card.extractfile(name).read()
    for number in (0,1):
        result=json.loads(read(f'pre-{number}/result.json'))
        check(result['bytes']==1048576 and result['sha256']=='1c4995ada54f944265c11f346177708351b4ff5a1003ba232f7e39b6a74b89bd','flash identity')
        check(b'guard_changes=0' in read(f'pre-{number}/status.txt'),'flash guards')
    games=json.loads(read('run/games.json'))
    details=[]
    for game in games[2:]:
        number=game['game_run'];prefix=f'run/persist/game-{number:04d}/'
        rows=[json.loads(line) for line in read(prefix+'live-frame-receipts.jsonl').splitlines()]
        check(game['idle_verified'] and game['key_sent']==game['key_acked'],'game cleanup/key ACK')
        check(len(rows)==game['frames'] and sum(r['paired_pio'] for r in rows)==4,'full frame/PIO count')
        for i,row in enumerate(rows):
            check(row['local_frame']==i+1 and row['game_run']==number,'local frame/run order')
            if i:check(row['generation']==rows[i-1]['generation']+1,'generation sequence')
            receipts[row['generation']]=row
        check(b'guard_changes=0' in read(prefix+'dma-pin-latest.txt'),'DMA guards')
        check(digest(read(prefix+'game-frame.bin'))==game['frame_sha256'],'final full frame')
        details.append(dict(run=number,frames=len(rows),paired_pio=4,keys_acked=game['key_acked'],idle_verified=True))

with tarfile.open(root/'deployment.tar.xz') as deployment:
    manifest=json.load(deployment.extractfile('gateway-manifest.json'))
    wheel=next((root/'dependencies').glob('*.whl')).read_bytes()
    with zipfile.ZipFile(io.BytesIO(wheel)) as library:
        for name, expected in manifest.items():
            if name.startswith('vendor/'):
                data=library.read(name[len('vendor/'):])
            elif name.endswith('.whl'):
                data=wheel
            else:
                data=deployment.extractfile(name).read()
            check(digest(data)==expected,'deployment identity: '+name)
    journal=[json.loads(line) for line in deployment.extractfile('transport.jsonl')]
    sent=[row for row in journal if row['type']=='frame']
    for row in sent:
        check(row['inflight']<=2,'video credit bound')
        compare(receipts,int(row['frame'].split('-')[1]),row['sha256'])

client_count=0
comparison={}
for place in ('local','mac'):
    samples=json.loads((root/f'{place}-abba-final.json').read_text())
    result={}
    check([r['mode'] for r in samples]==['http','stream','stream','http'],'ABBA order')
    for sample in samples:
        for row in sample['frames']:
            compare(receipts,row['generation'],row['sha256']);client_count+=1
    for mode in ('http','stream'):
        runs=[r for r in samples if r['mode']==mode]
        values=[t['ms'] for run in runs for t in run['trials']]
        result[mode]=dict(trials=len(values),median_ms=statistics.median(values),max_ms=max(values),
            mean_run_fps=statistics.mean(r['delivered_fps'] for r in runs),fps_runs=[r['delivered_fps'] for r in runs])
    result['latency_reduction_percent']=(1-result['stream']['median_ms']/result['http']['median_ms'])*100
    result['delivery_fps_increase_percent']=(result['stream']['mean_run_fps']/result['http']['mean_run_fps']-1)*100
    comparison[place]=result
check(comparison==json.loads((root/'comparison.json').read_text()),'measurement replay')
life=json.loads((root/'lifecycle.json').read_text())
check(life['stalled_video_close_code']==1008 and life['stale_rejected'] and life['disconnect_release_confirmed'] and life['sequence_gap_rejected'],'physical lifetime gates')
rejected=0
for generation, sha in ((-1,'0'*64),(next(iter(receipts)),'0'*64)):
    try:compare(receipts,generation,sha)
    except ValueError:rejected+=1
check(rejected==2,'tamper tests')
print(json.dumps(dict(games=details,full_frames=len(receipts),gateway_payloads=len(sent),
    matched_client_payloads=client_count,manifest_files=len(manifest),tamper_rejections=rejected,
    owner_bundle_unchanged=json.loads((root/'owner-identity.json').read_text())['accepted_bundle_unchanged']),indent=2))
