#!/usr/bin/env python3
"""Independently reconstruct persistent-session replay evidence on any host."""
import argparse,base64,hashlib,json,re,subprocess,zipfile
from pathlib import Path
from session import bio
from tetris_replay import next_request
from live_test import ROM_SHA

def verify_close(folder):
    before=(folder/'stage-before-a5.bin').read_bytes()
    assert len(before)==524288 and hashlib.sha256(before).hexdigest()==ROM_SHA
    for n in ['stage-before-5a.bin','stage-restored-a5.bin','stage-restored-5a.bin']:
        assert (folder/n).read_bytes()==before
    assert 'SESSION CLOSE rc=0 pending=0 exec-dirty=0 stage-dirty=0' in (folder/'result.txt').read_text()
    for names in [
        ['rom-table-a5.bin','rom-table-5a.bin','exec-table-restored-a5.bin','exec-table-restored-5a.bin'],
        ['exec-ram-before-a5.bin','exec-ram-before-5a.bin','exec-ram-restored-a5.bin','exec-ram-restored-5a.bin'],
        ['exec-flash-before-a5.bin','exec-flash-before-5a.bin','exec-flash-restored-a5.bin','exec-flash-restored-5a.bin'],
        ['upload-test.bin','upload-restore.bin','exec-flash-followup.bin','exec-stock-followup.bin']]:
        assert len({(folder/n).read_bytes() for n in names})==1,names
    return before

def validate(folder,code,oracle):
    before=verify_close(folder/'close')
    assert (folder/'open/stage-before-a5.bin').read_bytes()==before
    state=None;full_audits=0
    rows=[json.loads(line) for line in (folder/'progress.jsonl').read_text().splitlines()]
    with zipfile.ZipFile(folder/'steps.zip') as z:
        assert len(z.namelist())==3*len(rows)
        for i,row in enumerate(rows):
            kind,request=next_request(state,i)
            assert row['index']==i and row['kind']==kind and base64.b64decode(row['request'])==request
            expected=subprocess.run([str(oracle)],input=request,stdout=subprocess.PIPE,check=True).stdout
            image=bio.prepare(code,request,8192,i+1)
            original=image+before[len(image):]
            delta=z.read(f'{i:05d}/image.xor');n=len(delta)
            assert n in (bio.IMAGE_SIZE,524288) and n==row['audit_bytes']
            assert n==(524288 if (i+1)%32==0 else bio.IMAGE_SIZE)
            full_audits+=n==524288
            after=(int.from_bytes(delta,'little')^int.from_bytes(before[:n],'little')).to_bytes(n,'little')
            assert hashlib.sha256(after).hexdigest()==row['image_sha256']
            assert bio.response(original,after+before[n:])==(0,expected)
            assert after[bio.OFFSET:bio.IMAGE_SIZE]==z.read(f'{i:05d}/response.bin')
            assert hashlib.sha256(expected).hexdigest()==row['response_sha256']
            log=z.read(f'{i:05d}/result.txt').decode()
            submits=re.findall(r'^submit op=(\w+) id=(\d+)',log,re.M)
            completes=re.findall(r'^complete op=(\w+) id=(\w+) status=(\w+).*guard-changed=(\d+)',log,re.M)
            assert len(submits)==len(completes)==row['commands']
            assert len(submits)==(16 if i==0 else 28 if n==524288 else 12)
            for (op,tag),(cop,ctag,status,guard) in zip(submits,completes):
                assert op==cop and int(tag)==int(ctag,16) and guard=='0'
                assert int(status,16) in ([0x17d,0x17f] if op=='6f' else [0])
            assert sum(int(c[2],16)==0x17f for c in completes)==1
            assert f'audit_bytes={n}' in log
            state=expected[:240]
    summary=json.loads((folder/'summary.json').read_text())
    assert summary['steps']==len(rows) and summary['restored'] and summary['unloaded']
    return dict(valid=True,steps=len(rows),full_step_audits=full_audits,paired_payload_checks=len(rows),restored=True)
def validate_cadence(folder,code,oracle):
    before=verify_close(folder/'close');state=None
    summary=json.loads((folder/'summary.json').read_text())
    timings=json.loads((folder/'timing.json').read_text())
    assert len(timings)==summary['steps']
    with zipfile.ZipFile(folder/'steps.zip') as z:
        assert len(z.namelist())==3*len(timings)
        for i,row in enumerate(timings):
            assert row['index']==i
            kind,request=next_request(state,i)
            expected=subprocess.run([str(oracle)],input=request,stdout=subprocess.PIPE,check=True).stdout
            image=bio.prepare(code,request,8192,i+1)
            block=z.read(f'{i:05d}/response.bin')
            assert z.read(f'{i:05d}/request.bin')==image[bio.OFFSET:]
            assert bio.response(image+before[len(image):],image[:bio.OFFSET]+block+before[len(image):])==(0,expected)
            log=z.read(f'{i:05d}/result.txt').decode()
            assert f'SESSION STEP sequence={i+1} ' in log
            assert 'guard-changed=1' not in log
            state=expected[:240]
    return dict(valid=True,steps=len(timings),restored=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('--payload',type=Path,required=True);p.add_argument('--oracle',type=Path,required=True);p.add_argument('--cadence',action='store_true');a=p.parse_args()
    fn=validate_cadence if a.cadence else validate
    print(json.dumps(fn(a.folder,a.payload.read_bytes(),a.oracle),indent=2))
