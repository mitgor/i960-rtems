#!/usr/bin/env python3
"""Reject altered STOP, stack, owner and full-flash evidence."""
import json,shutil,struct,tempfile,sys
from pathlib import Path
from verify_live import check_run,owners,read,verify
from run_lease import NONCE,fnv

def rejected(action):
    try:action()
    except ValueError:return
    raise AssertionError('tampered evidence accepted')

def main(root,acceptance):
    verify(root,acceptance)
    live=root/'accept-1'
    before=(live/'page-before.bin').read_bytes()
    reserved=(live/'page-reserved.bin').read_bytes()
    image=(Path(__file__).resolve().parent/'image.bin').read_bytes()
    digest=fnv(image)
    page=bytearray((live/'stop/page-after.bin').read_bytes())
    page[0xa54]^=1
    rejected(lambda:check_run(bytes(page),before,reserved,0xc0710000,digest,'stop'))
    page=bytearray((live/'timeout/page-after.bin').read_bytes())
    page[0xa6c]^=1
    rejected(lambda:check_run(bytes(page),before,reserved,0xc0710000,digest,'timeout'))
    owner=bytearray((live/'owner-after.bin').read_bytes())
    owner[0x6a0]^=1
    rejected(lambda:owners((live/'owner-before.bin').read_bytes(),bytes(owner)))
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp);source=root/'postcall-flash'
        for name in ('request.json','result.json','status.txt','data.bin'):
            shutil.copyfile(source/name,path/name)
        data=bytearray((path/'data.bin').read_bytes());data[0xe000]^=1
        (path/'data.bin').write_bytes(data)
        rejected(lambda:read(path))
    return {'tamper_cases_rejected':4}

if __name__=='__main__':
    print(json.dumps(main(Path(sys.argv[1]),Path(sys.argv[2])),indent=2))
