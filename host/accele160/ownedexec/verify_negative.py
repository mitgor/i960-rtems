#!/usr/bin/env python3
"""Replay rejected owned-RAM call captures and unchanged result sentinels."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

_pagecopy = Path(__file__).resolve().parents[1] / 'pagecopy/verify_live.py'
_spec = importlib.util.spec_from_file_location('accele_pagecopy_replay_owned', _pagecopy)
_copy = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_copy)
fnv, verify_grant = _copy.fnv, _copy.verify_grant
PROBE_SHA='5d86878199ddcdd7f7ea950699a8e047f4189eb264c1dcff860ee6f83e0e740c'
PROBE=Path(__file__).with_name('probe.bin').read_bytes()
assert len(PROBE)==80 and hashlib.sha256(PROBE).hexdigest()==PROBE_SHA


def verify(path: Path, mode: str) -> dict:
    if mode not in ("bad-hash", "bad-code"): raise ValueError("mode")
    result=verify_grant(path)
    read=lambda n:(path/f'{n}.bin').read_bytes()
    before,reserved=read('page-before'),read('page-reserved')
    if read('page-restored')!=before or read('staging-restored')!=read('staging-before'):
        raise ValueError('restoration')
    payload=[]
    for index in (0,1):
        pattern=bytes(((i*53+0x96+index)^(i>>3))&0xff for i in range(4096))
        if index==0:
            probe=bytearray(PROBE)
            if mode=="bad-code":probe[0x38]^=1
            pattern=bytes(probe)+pattern[80:]
        if read(f'staging-{index}-readback')!=pattern:raise ValueError('staging readback')
        page=read(f'copy-{index}-page')
        digest=fnv(pattern)
        if len(page)!=4096 or struct.unpack_from('<4I',page,0x820)!=(0x59504f43,0x16161061,index,digest) or \
           struct.unpack_from('<4I',page,0x860)!=(0x59504f43,0x16161061,index,digest):
            raise ValueError('copy result')
        expected=bytearray(reserved)
        expected[0x820:0x830]=page[0x820:0x830]
        expected[0x860:0x870]=page[0x860:0x870]
        if page!=expected:raise ValueError('copy page drift')
        st=dict(x.split('=',1) for x in (path/f'copy-{index}-status.txt').read_text().split())
        if any(st.get(k)!=v for k,v in [('started','1'),('done','1'),('status','0'),('residual','0')]):
            raise ValueError('copy status')
        payload.append(pattern)
    whole=fnv(b''.join(payload)); ptr=int(result['pointer'],16)
    digest_page=read('digest-page')
    if struct.unpack_from('<4I',digest_page,0x830)!=(0x48534148,0x16161071,2,whole) or \
       struct.unpack_from('<4I',digest_page,0x870)!=(0x48534148,0x16161071,2,whole):
        raise ValueError('digest report')
    expected=bytearray(reserved)
    expected[0x820:0x830]=before[0x820:0x830]
    expected[0x830:0x840]=digest_page[0x830:0x840]
    expected[0x870:0x880]=digest_page[0x870:0x880]
    if digest_page!=expected:raise ValueError('digest page drift')
    st=dict(x.split('=',1) for x in (path/'digest-status.txt').read_text().split())
    if any(st.get(k)!=v for k,v in [('started','1'),('done','1'),('status','0'),('residual','0')]):
        raise ValueError('digest status')
    executed=read('ownedexec-page')
    requested=whole ^ (1 if mode=='bad-hash' else 0)
    if executed[0x800:0x810]!=b'\xa5'*16 or executed[0x830:0x840]!=b'\xa5'*16 or \
       struct.unpack_from('<4I',executed,0x880)!=(0x43455845,0x16161081,2,requested):
        raise ValueError('rejected code modified result/report or control')
    expected=bytearray(reserved)
    expected[0x820:0x830]=before[0x820:0x830]
    expected[0x800:0x810]=b'\xa5'*16
    expected[0x830:0x840]=b'\xa5'*16
    expected[0x880:0x890]=executed[0x880:0x890]
    if executed!=expected:raise ValueError('owned call changed unrelated loader bytes')
    st=dict(x.split('=',1) for x in (path/'ownedexec-status.txt').read_text().split())
    if any(st.get(k)!=v for k,v in [('started','1'),('done','1'),('status','2'),('residual','0')]):
        raise ValueError('owned execution rejection status')
    host=json.loads((path/'result.json').read_text())
    if host['whole_digest']!=f'0x{whole:08x}' or host['probe_sha256']!=PROBE_SHA or host['mode']!=mode or not host['execution_rejected'] or not all(
        host[k] for k in ('metadata_restored','loader_page_restored','staging_restored')):
        raise ValueError('host result')
    result.update(entry=f'0x{ptr:08x}',image_bytes=8192,whole_digest=f'0x{whole:08x}',mode=mode,rejected_before_call=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('mode',choices=('bad-hash','bad-code'));a=p.parse_args()
    print(json.dumps(verify(a.capture,a.mode),indent=2))
