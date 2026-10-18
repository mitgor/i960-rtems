#!/usr/bin/env python3
"""Verify archived investigation records and their current native sources."""
import hashlib
import json
from pathlib import Path
import tarfile

here=Path(__file__).resolve().parent;root=here.parents[2]
archive=here/'evidence.tar.xz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='ed0f2d6a954598443fe9b731096ed443b48336c61347b7e638c4ecaedfff8cd8'
with tarfile.open(archive) as t:
    for prefix in ('native','native-asan'):
        r=json.load(t.extractfile(prefix+'/result.json'))
        for name,digest in r['sources'].items():
            assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
        out=t.extractfile(prefix+'/stdout.txt').read().decode()
        assert out==r['stdout'] and 'PASS three fresh-image epochs' in out
        for epoch,exit,frames in ((1,'owner-stop',64),(2,'menu-quit',42),(3,'owner-stop',64)):
            assert f'epoch={epoch} stop={exit} frames={frames}' in out
        assert not t.extractfile(prefix+'/stderr.txt').read()
    card=json.load(t.extractfile('card-state/result.json'))
    assert card['piatvr_restored'] and not card['card_commands_issued'] and not card['card_ram_writes']
    assert card['heartbeat_first']==card['heartbeat_second']==15733
    assert card['claim'][5:7]==['0x45495551','0x00000000'] and card['old']['driver'] is None
    reset=json.load(t.extractfile('reset-support.json'))
    assert reset['reset_method']=='pm' and reset['reset_attempted'] is False
print('PASS archived STOP/Quit/STOP native proofs, source hashes, sanitizer log and non-destructive card snapshot')
