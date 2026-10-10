#!/usr/bin/env python3
"""Validate full live staging captures and command transcript, offline only."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]

def validate(directory):
    plan = json.loads((ROOT/'artifacts/romhook-20261010/stage-plan/stage-plan.json').read_text())
    captures = directory/'captures'
    result = (captures/'result.txt').read_text()
    hashes = {}
    images = {}
    for phase, expected in [('before',plan['stock_sha256']), ('candidate',plan['candidate_sha256']), ('restored',plan['stock_sha256'])]:
        a = (captures/f'stage-{phase}-a5.bin').read_bytes()
        b = (captures/f'stage-{phase}-5a.bin').read_bytes()
        assert len(a) == len(b) == 524288 and a == b, phase
        digest = hashlib.sha256(a).hexdigest()
        assert digest == expected, (phase,digest)
        hashes[phase] = digest
        images[phase] = a
    assert images['before'] == images['restored']
    expected = bytearray(images['before'])
    for patch in plan['patches']:
        off, size = patch['offset'],patch['length']
        assert expected[off:off+size] == bytes.fromhex(patch['before_hex'])
        expected[off:off+size] = bytes.fromhex(patch['after_hex'])
    assert bytes(expected) == images['candidate']
    submits = re.findall(r'^submit op=([0-9a-f]+) id=(\d+) len=(\d+) offset=([0-9a-f]+)', result, re.M)
    completes = re.findall(r'^complete op=([0-9a-f]+) id=([0-9a-f]+) status=([0-9a-f]+) changed=\d+ guard-changed=(\d+)', result, re.M)
    assert len(submits) == len(completes) == 74
    for num,(submit,complete) in enumerate(zip(submits,completes),1):
        op,tag,count,offset = submit
        cop,ctag,status,guard = complete
        assert op == cop and int(tag) == int(ctag,16) == num
        assert int(status,16) == 0 and int(guard) == 0
        assert op in ('1c','20','21')
    uploads = [(int(count),int(offset,16)) for op,tag,count,offset in submits if op == '21']
    assert uploads == [(p['length'],p['offset']) for p in plan['patches']]*2
    for marker in ('experiment-result=0 pending=0','stage-dirty=0','scratch-dirty=0','exec-dirty=0',
                   'RESTORED full staging image to exact original stock bytes'):
        assert marker in result, marker
    assert 'uncertain completion' not in result and 'REBOOT REQUIRED' not in result
    return dict(result='passed', paired_full_images=3, image_bytes=524288,
                sha256=hashes, completed_commands=74, uploads=6,
                patch_bytes=56, changed_bytes=sum(a!=b for a,b in zip(images['before'],images['candidate'])),
                full_stock_restored=True, flash_programmed=False, recovery_tested=False,
                cpu_view_of_candidate_verified=False)

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',nargs='?',type=Path,default=ROOT/'artifacts/staging-rehearsal-20261010')
    args=parser.parse_args()
    print(json.dumps(validate(args.directory),indent=2))
