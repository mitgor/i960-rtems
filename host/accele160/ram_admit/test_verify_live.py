#!/usr/bin/env python3
"""Reject altered flash, report, manifest and owner captures."""
import shutil, tempfile
from pathlib import Path

from verify_live import (IMAGE_SHA, NONCE, check_accepted, check_rejected,
                         owner_records, read, verify)
from run_admit import fnv

def rejects(action):
    try: action()
    except ValueError: return
    raise AssertionError('tampered capture accepted')

def main(root):
    verify(root)
    live=root/'ram-admit'
    run=live/'run'
    before=(run/'page-before.bin').read_bytes()
    reserved=(run/'page-reserved.bin').read_bytes()
    owned=(run/'owner-reserved.bin').read_bytes()
    child=run/'run-1'
    page=bytearray((child/'page-after.bin').read_bytes())
    digest=fnv((child/'stage-readback.bin').read_bytes())
    page[0xa38]^=1
    rejects(lambda:check_accepted(bytes(page),before,reserved,0xc0710000,
                                  NONCE,digest,0x16010001))
    negative=bytearray((child/'bad-hash/page.bin').read_bytes())
    negative[0xa20]^=1
    rejects(lambda:check_rejected(bytes(negative),before,reserved,NONCE,
                                  0xc0710000,digest,'bad-hash'))
    owner=bytearray((child/'owner-after.bin').read_bytes())
    owner[0x6a0]^=1
    rejects(lambda:owner_records(owned,bytes(owner)))
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)
        source=live/'persistent-0'
        for name in ('request.json','result.json','status.txt','data.bin'):
            shutil.copyfile(source/name,path/name)
        image=bytearray((path/'data.bin').read_bytes())
        image[0xe000]^=1
        (path/'data.bin').write_bytes(image)
        rejects(lambda:read(path,IMAGE_SHA))
    return dict(tamper_cases_rejected=4)

if __name__=='__main__':
    import json,sys
    print(json.dumps(main(Path(sys.argv[1])),indent=2))
