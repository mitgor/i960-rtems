#!/usr/bin/env python3
"""Offline validation of the CPU-side staging rehearsal."""
from pathlib import Path
import hashlib,json,re,zlib
ROOT=Path(__file__).resolve().parents[2]

def validate(base=None):
    if base is None: base=ROOT/'artifacts/programming-preflight-20261010'
    cap=base/'captures'
    text=(cap/'result.txt').read_text()
    stock=(ROOT/'artifacts/private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin').read_bytes()
    candidate=(ROOT/'artifacts/romhook-20261010/candidate-full-rom.bin').read_bytes()
    for phase,expected in [('before',stock),('candidate',candidate),('restored',stock)]:
        for pat in ('a5','5a'): assert (cap/f'stage-{phase}-{pat}.bin').read_bytes()==expected
    for site,code in [('ram',(ROOT/'loader/romfetch/ram-status.bin').read_bytes()),('flash',(base/'build/probe.bin').read_bytes())]:
        before=(cap/f'exec-{site}-before-a5.bin').read_bytes()
        assert len(before)==128
        for pat in ('a5','5a'):
            assert (cap/f'exec-{site}-before-{pat}.bin').read_bytes()==before
            assert (cap/f'exec-{site}-restored-{pat}.bin').read_bytes()==before
            assert (cap/f'exec-{site}-after-{pat}.bin').read_bytes()==code+before[len(code):]
    for pat in ('a5','5a'):
        assert (cap/f'rom-table-{pat}.bin').read_bytes()==bytes.fromhex('98fe01c0')
        assert (cap/f'exec-table-restored-{pat}.bin').read_bytes()==bytes.fromhex('98fe01c0')
        assert (cap/f'exec-table-ram-{pat}.bin').read_bytes()==bytes.fromhex('00c1fac0')
        assert (cap/f'exec-table-flash-{pat}.bin').read_bytes()==bytes.fromhex('80c1fac0')
    submits=re.findall(r'^submit op=(\w+) id=(\d+) len=(\d+) offset=(\w+)',text,re.M)
    completes=re.findall(r'^complete op=(\w+) id=(\w+) status=(\w+) changed=\d+ guard-changed=(\d+)',text,re.M)
    assert len(submits)==len(completes)==105
    statuses=[]
    for num,(s,c) in enumerate(zip(submits,completes),1):
        assert s[0]==c[0] and int(s[1])==int(c[1],16)==num and int(c[3])==0
        assert s[0] in ('1c','20','21','6f')
        if s[0]=='6f': statuses.append(int(c[2],16))
        else: assert c[2]=='0000'
    assert statuses==[0x17e,0x17f,0x104]
    plan=json.loads((ROOT/'artifacts/romhook-20261010/stage-plan/stage-plan.json').read_text())
    patch=[(p['length'],p['offset']) for p in plan['patches']]
    extra=[(24,0x80100),(4,0xff0f39bc),(128,0x80180),(4,0xff0f39bc),(4,0xff0f39bc),(24,0x80100),(128,0x80180)]
    assert [(int(n),int(off,16)) for op,tag,n,off in submits if op=='21']==patch+extra+patch
    for marker in ['experiment-result=0 pending=0','stage-dirty=0','exec-dirty=0','scratch-dirty=0','CPU CRC32 of full candidate through C1F2C000 equals 2012d01f']:
        assert marker in text
    return dict(result='passed',commands=105,cpu_source='C1F2C000',cpu_bytes=524288,
                cpu_crc32=f'{zlib.crc32(candidate):08x}',candidate_sha256=hashlib.sha256(candidate).hexdigest(),
                completion_statuses=[f'{s:04x}' for s in statuses],
                full_stock_restored=True,dispatch_and_code_restored=True,
                prior_dcache_invalidation=True,alias_intrinsically_uncached_proven=False,
                flash_programmed=False,recovery_tested=False)

if __name__=='__main__': print(json.dumps(validate(),indent=2))
