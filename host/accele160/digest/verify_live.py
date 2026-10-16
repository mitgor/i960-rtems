#!/usr/bin/env python3
"""Replay two-page upload and contiguous on-card digest captures."""
import argparse
import json
from pathlib import Path
import struct
import importlib.util
_pagecopy_path = Path(__file__).resolve().parents[1] / "pagecopy/verify_live.py"
_spec = importlib.util.spec_from_file_location("accele_pagecopy_replay", _pagecopy_path)
_pagecopy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pagecopy)
fnv = _pagecopy.fnv
verify_grant = _pagecopy.verify_grant


def verify(path: Path):
    result = verify_grant(path)
    get = lambda name: (path / f'{name}.bin').read_bytes()
    before, reserved = get('page-before'), get('page-reserved')
    if get('page-restored') != before or get('staging-restored') != get('staging-before'):
        raise ValueError('restoration')
    payload=[]
    for index in (0,1):
        pattern=bytes(((i*53+0x96+index)^(i>>3))&0xff for i in range(4096))
        if get(f'staging-{index}-readback') != pattern:
            raise ValueError('staging readback')
        page=get(f'copy-{index}-page')
        digest=fnv(pattern)
        if len(page)!=4096 or struct.unpack_from('<4I',page,0x820)!=(0x59504f43,0x16161061,index,digest) or \
           struct.unpack_from('<4I',page,0x860)!=(0x59504f43,0x16161061,index,digest):
            raise ValueError('copy result')
        expected=bytearray(reserved)
        expected[0x820:0x830]=page[0x820:0x830]
        expected[0x860:0x870]=page[0x860:0x870]
        if page != expected:raise ValueError('copy page drift')
        st=dict(x.split('=',1) for x in (path/f'copy-{index}-status.txt').read_text().split())
        if any(st.get(k)!=v for k,v in [('started','1'),('done','1'),('status','0'),('residual','0')]):
            raise ValueError('copy command status')
        payload.append(pattern)
    whole=fnv(b''.join(payload))
    digest_page=get('digest-page')
    if len(digest_page)!=4096 or struct.unpack_from('<4I',digest_page,0x830)!=(0x48534148,0x16161071,2,whole) or \
       struct.unpack_from('<4I',digest_page,0x870)!=(0x48534148,0x16161071,2,whole):
        raise ValueError('card whole-image digest')
    expected=bytearray(reserved)
    expected[0x820:0x830]=before[0x820:0x830]
    expected[0x830:0x840]=digest_page[0x830:0x840]
    expected[0x870:0x880]=digest_page[0x870:0x880]
    if digest_page!=expected:raise ValueError('digest page drift')
    st=dict(x.split('=',1) for x in (path/'digest-status.txt').read_text().split())
    if any(st.get(k)!=v for k,v in [('started','1'),('done','1'),('status','0'),('residual','0')]):
        raise ValueError('digest command status')
    host=json.loads((path/'result.json').read_text())
    if host['indexes']!=[0,1] or host['whole_digest']!=f'0x{whole:08x}' or not all(
      host[k] for k in ('metadata_restored','loader_page_restored','staging_restored')):
        raise ValueError('host result')
    result.update(image_bytes=8192,contiguous_pages=2,whole_digest=f'0x{whole:08x}',digest_passed=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args()
    print(json.dumps(verify(a.capture),indent=2))
