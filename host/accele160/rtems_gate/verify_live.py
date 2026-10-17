#!/usr/bin/env python3
"""Replay pinned AcceleRAID RTEMS software-clock captures and full audits."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import tempfile

_copy_path=Path(__file__).resolve().parents[1]/'pagecopy/verify_live.py'
_spec=importlib.util.spec_from_file_location('accele_pagecopy_replay_rtems',_copy_path)
_copy=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_copy)
fnv,verify_grant=_copy.fnv,_copy.verify_grant
PAGES=15
PAGE=4096
FIRMWARE_SHA='68451b38b96609fa3a95eb9497fe85a34ac92fec45b912c53612969b1209a988'
PAYLOAD_SHA='318b9f70fe021ce1fb18e3c75465d9231cb55c3ca6893d99511b9b73c383adc0'
FNV=0x648486da
BOOT='ccdf3abd-8148-45f7-868b-369c5f26a7e9'

def status(path):
    return dict(x.split('=',1) for x in path.read_text().split())

def need_status(path, expected):
    s=status(path)
    if any(s.get(k)!=v for k,v in [('started','1'),('done','1'),('status',str(expected)),('residual','0')]):
        raise ValueError(f'command status: {path}')

def verify_flash(path, expected):
    req=json.loads((path/'request.json').read_text())
    result=json.loads((path/'result.json').read_text())
    blob=(path/'data.bin').read_bytes()
    st=status(path/'status.txt')
    if req.get('boot_id')!=BOOT or req.get('selector')!=9 or req.get('length')!=1048576 or \
       len(blob)!=1048576 or hashlib.sha256(blob).hexdigest()!=expected or result.get('sha256')!=expected or \
       any(st.get(k)!='0' for k in ('status','residual','guard_changes')) or \
       st.get('done')!='1' or st.get('selector')!='9' or st.get('length')!='1048576' or \
       req.get('card')!=result.get('card_after') or \
       result['old_after']['driver'] is not None or result['card_after']['driver']!='myrsread':
        raise ValueError(f'full-flash audit: {path}')

def verify(path:Path,payload:bytes) -> dict:
    if len(payload)!=PAGES*PAGE or hashlib.sha256(payload).hexdigest()!=PAYLOAD_SHA or fnv(payload)!=FNV:
        raise ValueError('payload identity')
    result=verify_grant(path)
    before=(path/'page-before.bin').read_bytes();reserved=(path/'page-reserved.bin').read_bytes()
    stage=(path/'stage-readbacks.bin').read_bytes();copies=(path/'copy-pages.bin').read_bytes()
    statuses=json.loads((path/'copy-statuses.json').read_text())
    if len(stage)!=PAGES*PAGE or len(copies)!=PAGES*PAGE or len(statuses)!=PAGES:raise ValueError('aggregate size')
    if (path/'staging-restored.bin').read_bytes()!=(path/'staging-before.bin').read_bytes() or \
       (path/'page-restored.bin').read_bytes()!=before:raise ValueError('restoration')
    for index in range(PAGES):
        pattern=payload[index*PAGE:(index+1)*PAGE]
        if stage[index*PAGE:(index+1)*PAGE]!=pattern:raise ValueError(f'staging {index}')
        page=copies[index*PAGE:(index+1)*PAGE];digest=fnv(pattern)
        if struct.unpack_from('<4I',page,0x820)!=(0x59504f43,0x16161061,index,digest) or \
           struct.unpack_from('<4I',page,0x860)!=(0x59504f43,0x16161061,index,digest):
            raise ValueError(f'copy report {index}')
        expected=bytearray(reserved);expected[0x820:0x830]=page[0x820:0x830];expected[0x860:0x870]=page[0x860:0x870]
        if page!=expected:raise ValueError(f'copy loader drift {index}')
        st=statuses[index]
        if st['index']!=index or st['elapsed_ms']<0 or any(st['status'].get(k)!=v for k,v in [('started','1'),('done','1'),('status','0'),('residual','0')]):
            raise ValueError(f'copy status {index}')
    digest_page=(path/'digest-page.bin').read_bytes()
    if struct.unpack_from('<4I',digest_page,0x830)!=(0x48534148,0x16161071,PAGES,FNV) or \
       struct.unpack_from('<4I',digest_page,0x870)!=(0x48534148,0x16161071,PAGES,FNV):
        raise ValueError('full digest')
    expected=bytearray(reserved);expected[0x820:0x830]=before[0x820:0x830];expected[0x830:0x840]=digest_page[0x830:0x840];expected[0x870:0x880]=digest_page[0x870:0x880]
    if digest_page!=expected:raise ValueError('digest loader drift')
    need_status(path/'digest-status.txt',0)
    for label,count,hash_value in (('bad-hash',PAGES,FNV^1),('bad-count',PAGES-1,FNV)):
        page=(path/f'{label}-page.bin').read_bytes()
        if page[0x800:0x820]!=b'\xa5'*32 or page[0x830:0x840]!=b'\xa5'*16 or \
           struct.unpack_from('<4I',page,0x890)!=(0x39544552,0x16161091,count,hash_value):
            raise ValueError(f'{label} changed report or control')
        expected=bytearray(reserved);expected[0x820:0x830]=before[0x820:0x830];expected[0x800:0x820]=b'\xa5'*32;expected[0x830:0x840]=b'\xa5'*16;expected[0x890:0x8a0]=page[0x890:0x8a0]
        if page!=expected:raise ValueError(f'{label} loader drift')
        need_status(path/f'{label}-status.txt',2)
    ptr=int(result['pointer'],16)
    page=(path/'rtems-page.bin').read_bytes()
    if struct.unpack_from('<8I',page,0x800)!=(0x4d455452,0x16161091,0x46600006,1,5,11,0xc071e270,0x1600a001) or \
       struct.unpack_from('<4I',page,0x830)!=(0x214d4552,0x16161091,ptr,FNV) or \
       struct.unpack_from('<4I',page,0x890)!=(0x39544552,0x16161091,PAGES,FNV):
        raise ValueError('RTEMS report')
    expected=bytearray(reserved);expected[0x820:0x830]=before[0x820:0x830];expected[0x800:0x820]=page[0x800:0x820];expected[0x830:0x840]=page[0x830:0x840];expected[0x890:0x8a0]=page[0x890:0x8a0]
    if page!=expected:raise ValueError('RTEMS loader drift')
    need_status(path/'rtems-status.txt',0)
    host=json.loads((path/'result.json').read_text())
    if not host['rtems_executed'] or host['pages']!=PAGES or host['whole_digest']!=f'0x{FNV:08x}' or \
       not all(host[k] for k in ('metadata_restored','loader_page_restored','staging_restored')) or \
       host['old_after']['driver'] is not None:raise ValueError('host summary')
    result.update(pages=PAGES,bytes_uploaded=len(payload),whole_digest=f'0x{FNV:08x}',
                  upload_elapsed_s=host['upload_elapsed_s'],rtems_observation_s=host['rtems_elapsed_s'],
                  software_tick_wakeup=5,rejections=['bad-hash','bad-count'])
    return result

def self_test(path,payload):
    for filename,offset in [('stage-readbacks.bin',7*PAGE+12),('copy-pages.bin',3*PAGE+0x828),('rtems-page.bin',0x814),('table-after.bin',0x2a0),('bad-hash-status.txt',None)]:
        with tempfile.TemporaryDirectory() as tmp:
            clone=Path(tmp)/'capture';shutil.copytree(path,clone)
            f=clone/filename;data=bytearray(f.read_bytes())
            if offset is None:data=data.replace(b'status=2',b'status=0',1)
            else:data[offset]^=1
            f.write_bytes(data)
            try:verify(clone,payload)
            except ValueError:pass
            else:raise AssertionError(f'mutation accepted: {filename}')
    return 5

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('payload',type=Path);p.add_argument('--self-test',action='store_true');a=p.parse_args()
    print(json.dumps(verify(a.capture,a.payload.read_bytes()),indent=2))
    if a.self_test:print('mutations_rejected',self_test(a.capture,a.payload.read_bytes()))
