#!/usr/bin/env python3
"""Replay 77-page owned upload, per-page checks and full card digest."""
import argparse
import importlib.util
import json
from pathlib import Path
import struct

_copy_path=Path(__file__).resolve().parents[1]/'pagecopy/verify_live.py'
_spec=importlib.util.spec_from_file_location('accele_pagecopy_replay_bulk',_copy_path)
_copy=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_copy)
fnv,verify_grant=_copy.fnv,_copy.verify_grant
PAGES=77
PAGE=4096


def verify(path: Path) -> dict:
    result=verify_grant(path)
    before=(path/'page-before.bin').read_bytes()
    reserved=(path/'page-reserved.bin').read_bytes()
    stage=(path/'stage-readbacks.bin').read_bytes()
    copies=(path/'copy-pages.bin').read_bytes()
    statuses=json.loads((path/'copy-statuses.json').read_text())
    if len(stage)!=PAGES*PAGE or len(copies)!=PAGES*PAGE or len(statuses)!=PAGES:
        raise ValueError('aggregate capture length')
    if (path/'staging-restored.bin').read_bytes()!=(path/'staging-before.bin').read_bytes() or \
       (path/'page-restored.bin').read_bytes()!=before:
        raise ValueError('staging or loader restoration')
    image=[]
    for index in range(PAGES):
        pattern=bytes(((i*53+0x96+index)^(i>>3))&0xff for i in range(PAGE))
        if stage[index*PAGE:(index+1)*PAGE]!=pattern:
            raise ValueError(f'staging readback page {index}')
        page=copies[index*PAGE:(index+1)*PAGE]
        digest=fnv(pattern)
        if struct.unpack_from('<4I',page,0x820)!=(0x59504f43,0x16161061,index,digest) or \
           struct.unpack_from('<4I',page,0x860)!=(0x59504f43,0x16161061,index,digest):
            raise ValueError(f'copy result page {index}')
        expected=bytearray(reserved)
        expected[0x820:0x830]=page[0x820:0x830]
        expected[0x860:0x870]=page[0x860:0x870]
        if page!=expected:raise ValueError(f'loader drift page {index}')
        st=statuses[index]
        if st['index']!=index or st['elapsed_ms']<0 or any(st['status'].get(k)!=v for k,v in
             [('started','1'),('done','1'),('status','0'),('residual','0')]):
            raise ValueError(f'copy status page {index}')
        image.append(pattern)
    whole=fnv(b''.join(image))
    digest_page=(path/'digest-page.bin').read_bytes()
    if struct.unpack_from('<4I',digest_page,0x830)!=(0x48534148,0x16161071,PAGES,whole) or \
       struct.unpack_from('<4I',digest_page,0x870)!=(0x48534148,0x16161071,PAGES,whole):
        raise ValueError('whole digest report')
    expected=bytearray(reserved)
    expected[0x820:0x830]=before[0x820:0x830]
    expected[0x830:0x840]=digest_page[0x830:0x840]
    expected[0x870:0x880]=digest_page[0x870:0x880]
    if digest_page!=expected:raise ValueError('digest page drift')
    st=dict(x.split('=',1) for x in (path/'digest-status.txt').read_text().split())
    if any(st.get(k)!=v for k,v in [('started','1'),('done','1'),('status','0'),('residual','0')]):
        raise ValueError('digest command status')
    host=json.loads((path/'result.json').read_text())
    if host['pages']!=PAGES or host['image_bytes']!=PAGES*PAGE or host['whole_digest']!=f'0x{whole:08x}' or not all(
        host[k] for k in ('metadata_restored','loader_page_restored','staging_restored')):
        raise ValueError('host summary')
    result.update(pages=PAGES,image_bytes=PAGES*PAGE,whole_digest=f'0x{whole:08x}',
                  upload_elapsed_s=host['upload_elapsed_s'],digest_elapsed_s=host['digest_elapsed_s'],
                  aggregate_audit_passed=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args()
    print(json.dumps(verify(a.capture),indent=2))
