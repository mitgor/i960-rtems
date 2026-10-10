#!/usr/bin/env python3
"""Validate the archived programming evidence, optionally including postboot."""
from pathlib import Path
import argparse,hashlib,json,re
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'artifacts/programmed-rom-20261010'

def validate(postboot=False):
    candidate=(ROOT/'artifacts/romhook-20261010/candidate-full-rom.bin').read_bytes()
    stock=(ROOT/'artifacts/private-dumps/snapshot-fresh-20261010T125336Z/image-window-0.bin').read_bytes()
    cap=BASE/'programming/captures'
    for pat in ('a5','5a'):
        assert (cap/f'stage-before-{pat}.bin').read_bytes()==stock
        assert (cap/f'stage-candidate-{pat}.bin').read_bytes()==candidate
        flash=(cap/f'flash-readback-{pat}.bin').read_bytes()
        assert flash==candidate and flash[0x7c000:]==stock[0x7c000:]
    text=(cap/'result.txt').read_text()
    assert text.count('PROGRAM SUBMITTED once:')==1
    assert 'PROGRAM SUBMITTED once: op=2b id=84 subcommand=1 bootblock=0' in text
    assert 'program transport rc=0 submitted=1 completed=1 pending=0' in text
    assert 'program-state=8 rc=0 submitted=1 completed=1 verified=1' in text
    assert 'experiment-result=0 pending=0 stage-dirty=0 exec-dirty=0' in text
    submissions=re.findall(r'^submit op=(\w+) id=(\d+)',text,re.M)
    completions=re.findall(r'^complete op=(\w+) id=(\w+) status=(\w+) changed=\d+ guard-changed=(\d+)',text,re.M)
    assert len(submissions)==len(completions)==101
    assert [int(s[1]) for s in submissions]==list(range(1,84))+list(range(85,103))
    ping_status=[]
    for s,c in zip(submissions,completions):
        assert s[0]==c[0] and int(s[1])==int(c[1],16) and c[3]=='0'
        if s[0]=='6f': ping_status.append(c[2])
        else: assert c[2]=='0000'
    assert ping_status==['017e','017f','0104']
    for pat in ('a5','5a'):
        assert (cap/f'exec-table-restored-{pat}.bin').read_bytes()==bytes.fromhex('98fe01c0')
        for site in ('ram','flash'):
            assert (cap/f'exec-{site}-restored-{pat}.bin').read_bytes()==(cap/f'exec-{site}-before-a5.bin').read_bytes()
    assert not re.search(r'guard-changed=[1-9]',text)
    tail=text.split('PROGRAM SUBMITTED once:',1)[1]
    assert not re.search(r'^submit op=(21|6f)',tail,re.M)
    report=dict(result='passed',programming_submissions=1,full_readback_bytes=len(candidate),
                sha256=hashlib.sha256(candidate).hexdigest(),boot_block_unchanged=True)
    if postboot:
        cap=BASE/'postboot/captures';text=(cap/'result.txt').read_text()
        for phase in ('before','restored'):
            for pat in ('a5','5a'):
                assert (cap/f'stage-{phase}-{pat}.bin').read_bytes()==candidate
        for pat in ('a5','5a'):
            assert (cap/f'rom-table-{pat}.bin').read_bytes()==bytes.fromhex('1c00fefe')
        submits=re.findall(r'^submit op=(\w+) id=(\d+)',text,re.M)
        completes=re.findall(r'^complete op=(\w+) id=(\w+) status=(\w+) changed=\d+ guard-changed=(\d+)',text,re.M)
        assert len(submits)==len(completes)==54
        for i,(s,c) in enumerate(zip(submits,completes),1):
            assert s[0]==c[0] and int(s[1])==int(c[1],16)==i
            assert s[0] in ('1c','20','6f') and c[3]=='0'
            assert c[2]==('017e' if s[0]=='6f' else '0000')
        assert sum(s[0]=='6f' for s in submits)==2
        assert 'experiment-result=0 pending=0' in text
        before=(BASE/'pre-program-state.txt').read_text()
        after=(BASE/'postboot-state.txt').read_text()
        uuid=r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        assert re.search(uuid,before)[0]!=re.search(uuid,after)[0]
        report.update(postboot_verified=True,postboot_commands=54,rom_handler='FEFE001C',ping_status='017E',ping_repetitions=2)
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--postboot',action='store_true')
    args=parser.parse_args();print(json.dumps(validate(args.postboot),indent=2))
