#!/usr/bin/env python3
"""Check that frame, command, and STOP tampering fail offline replay."""
import json,shutil,tempfile
from pathlib import Path
from verify_live import DEFAULT,verify

assert verify(DEFAULT)['commands']==232
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)/'capture';shutil.copytree(DEFAULT,root)
    path=root/'live-1/persist/frame.bin';data=bytearray(path.read_bytes())
    data[123]^=1;path.write_bytes(data)
    try:verify(root)
    except RuntimeError:pass
    else:raise AssertionError('frame mutation accepted')
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)/'capture';shutil.copytree(DEFAULT,root)
    path=root/'live-1/persist/bridge-receipts.json';data=json.loads(path.read_text())
    data[17]['value']+=1;path.write_text(json.dumps(data))
    try:verify(root)
    except RuntimeError:pass
    else:raise AssertionError('upload receipt mutation accepted')
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)/'capture';shutil.copytree(DEFAULT,root)
    path=root/'live-1/persist/quiescent-page.bin';data=bytearray(path.read_bytes())
    data[0xb54]^=1;path.write_bytes(data)
    try:verify(root)
    except RuntimeError:pass
    else:raise AssertionError('STOP mutation accepted')
print('three tamper cases rejected')
