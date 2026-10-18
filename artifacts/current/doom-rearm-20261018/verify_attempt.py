#!/usr/bin/env python3
"""Replay the failed first attempt and prove the staging-page false positive."""
import hashlib,json,struct,tarfile,zipfile
from pathlib import Path
p=Path(__file__).resolve().parent;root=p.parents[2]
sha=lambda b:hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(root/'artifacts/doom-m1-20261011/freedoom-0.13.0.zip') as z:
    name,=[n for n in z.namelist() if n.endswith('/freedoom1.wad')];wad=z.read(name)
with tarfile.open(p/'attempt-1.tar.xz') as t,tarfile.open(root/'artifacts/current/wide-screen-copy-20261018/first.tar.xz') as baseline:
    def read(n):return t.extractfile(n).read()
    base='sessions/20261018T103215Z/run/persist';d=base+'/game-0001'
    rows=[json.loads(x) for x in read(d+'/live-frame-receipts.jsonl').splitlines()]
    assert len(rows)==65
    for r in rows:
        n=r['generation'];b=read(d+f'/dma-frame-{n:04d}.bin')
        assert n==r['local_frame'] and r['slot']==(n-1)&1
        assert len(b)==77824 and b[:4096]==b'\xa5'*4096 and b[69664:]==b'\xa5'*8160
        assert sha(b[4096:69632])==r['sha256']
        assert struct.unpack_from('<8I',b,69632)==(0x31505044,0x161610e1,n,r['slot'],65536,r['source'],r['card_tick'],(~n)&0xffffffff)
        if n<=32:
            ref=baseline.extractfile(f'case/run/persist/live-frames/frame-{n:04d}.bin').read()
            assert b[4096:4096+64768]==ref[:64768] and r['paired_pio']
    for r in map(json.loads,read(d+'/engine-reads.jsonl').splitlines()):
        assert sha(wad[r['offset']:r['offset']+r['n']])==r['source_sha256']
    ready=read(base+'/ready-page.bin');stages=struct.unpack_from('<2I',ready,0xd38)
    delta=0xc0f41000-stages[1];assert delta>=0 and not delta%8192
    frame=read(d+'/live-frames/frame-0032.bin')
    assert (p/'tail-audit-diagnosis/page-1857.bin').read_bytes()==frame[delta//8192*4096:(delta//8192+1)*4096]
    final=read(base+'/failure-stop-page.bin');er=struct.unpack_from('<16I',final,0xc40)
    assert er[9:11]==(0,1) and er[11]==er[12] and struct.unpack_from('<2I',final,0xb54)==(0x45495551,0)
    for r in json.loads((p/'attempt-1-http/observations.json').read_text())['frames']:
        assert r['sha256']==rows[r['generation']-1]['sha256']
print('65 frames, first 32 accepted pictures, WAD/HTTP replay, exact staging-page identity and safe terminal STOP verified; zero rearms attempted')
