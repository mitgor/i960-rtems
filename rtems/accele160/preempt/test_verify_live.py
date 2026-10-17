#!/usr/bin/env python3
"""Replay succeeds and rejects four independent capture tamper cases."""
import shutil,sys,tempfile
from pathlib import Path
from verify_live import verify

def reject(root,rel,offset):
    with tempfile.TemporaryDirectory() as tmp:
        clone=Path(tmp)/'capture'
        shutil.copytree(root,clone)
        p=clone/rel;b=bytearray(p.read_bytes());b[offset]^=1;p.write_bytes(b)
        try:verify(clone)
        except ValueError:return
        raise AssertionError(f'tamper accepted: {rel}')

def main(root):
    root=Path(root);verify(root)
    for rel,off in (
        ('image/image.bin',0),
        ('live/after-accept1-flash-1/data.bin',0),
        ('live/accept-0/stop/page-after.bin',0xa4c),
        ('live/accept-1/owner-after.bin',0x2a0),
    ):reject(root,rel,off)
    print('baseline and four tamper rejections passed')

if __name__=='__main__':main(sys.argv[1])
