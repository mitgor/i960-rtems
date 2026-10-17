#!/usr/bin/env python3
"""Reject mutated flash, cached vector, STOP and owner captures."""
import shutil,sys,tempfile
from pathlib import Path
from verify_live import verify

source=Path(sys.argv[1])
verify(source)
mutations=(
 ('flash','timer-postflight-1/postcall-flash/data.bin',0),
 ('vector','timer-postflight-1/vector-page.bin',0x98c),
 ('stop-ack','timer-active-1/stop/page-after.bin',0xa54),
 ('owner','timer-active-1/owner-after.bin',0x2a0),
)
for label,relative,offset in mutations:
    with tempfile.TemporaryDirectory(prefix='accele160-timer-replay-') as tmp:
        dest=Path(tmp)/'capture';shutil.copytree(source,dest)
        target=dest/relative
        data=bytearray(target.read_bytes());data[offset]^=1
        target.write_bytes(data)
        try:verify(dest)
        except (ValueError,RuntimeError):print(label+': rejected')
        else:raise AssertionError(label+' mutation was accepted')
