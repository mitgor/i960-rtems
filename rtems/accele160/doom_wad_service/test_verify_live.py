#!/usr/bin/env python3
"""Mutation checks for offline capture replay."""
import json,shutil,tempfile
from pathlib import Path
from verify_live import DEFAULT,verify

assert verify(DEFAULT)['wad_requests']==42
for name,relative,change in (
    ('WAD receipt','evidence/persist/wad-receipts.json',
     lambda p: p.__setitem__('status',0)),
    ('bank audit','evidence/persist/ready-page.bin',None),
    ('STOP','evidence/persist/quiescent-page.bin',None),
):
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)/'capture';shutil.copytree(DEFAULT,root)
        path=root/relative
        if name=='WAD receipt':
            data=json.loads(path.read_text());change(data[37])
            path.write_text(json.dumps(data))
        else:
            data=bytearray(path.read_bytes())
            data[0xb04 if name=='bank audit' else 0xb54]^=1
            path.write_bytes(data)
        try:verify(root)
        except RuntimeError:pass
        else:raise AssertionError(f'{name} mutation accepted')
print('three capture mutations rejected')
