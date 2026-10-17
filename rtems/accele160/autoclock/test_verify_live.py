#!/usr/bin/env python3
"""Tamper checks for the accepted autonomous-clock capture replay."""
import shutil,sys,tempfile
from pathlib import Path
from verify_live import verify

root=Path(sys.argv[1]).resolve()
verify(root)
with tempfile.TemporaryDirectory(prefix='i960-autoclock-replay-') as temporary:
    trial=Path(temporary)/'artifact'
    shutil.copytree(root,trial)
    names=(
        'live/boot2-after-repeat-flash-1/data.bin',
        'live/accept-7/stop/page-after.bin',
        'live/accept-7-repeat/timeout/irq-stack-after.bin',
        'live/accept-7-repeat/owner-after.bin',
    )
    for name in names:
        p=trial/name;original=p.read_bytes();changed=bytearray(original)
        changed[len(changed)//2]^=1
        p.write_bytes(changed)
        try:verify(trial)
        except ValueError:pass
        else:raise AssertionError('tamper accepted: '+name)
        p.write_bytes(original)
        verify(trial)
print('baseline and four tamper cases passed')
