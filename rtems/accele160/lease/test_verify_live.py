#!/usr/bin/env python3
"""Mutation checks for the offline RTEMS lease evidence replay."""
import shutil,sys,tempfile
from pathlib import Path
from verify_live import verify

source=Path(sys.argv[1])
verify(source)
mutations=(
 ('flash','accept-3/postcall-flash/data.bin',0),
 ('stop-ack','accept-3/stop/page-after.bin',0xa54),
 ('restored-sp','accept-3/stop/page-after.bin',0xa6c),
 ('owner','accept-3/owner-after.bin',0x2a0),
)
for label,relative,offset in mutations:
    with tempfile.TemporaryDirectory(prefix='accele160-lease-replay-') as temp:
        dest=Path(temp)/'evidence'
        shutil.copytree(source,dest)
        path=dest/relative
        data=bytearray(path.read_bytes())
        data[offset]^=1
        path.write_bytes(data)
        try:verify(dest)
        except ValueError:print(label+': rejected')
        else:raise AssertionError(label+' mutation was accepted')
