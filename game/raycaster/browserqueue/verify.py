#!/usr/bin/env python3
"""Replay variable browser requests through the unchanged full queue verifier."""
import argparse
import json
import sys
from pathlib import Path
if not __debug__:
    raise SystemExit('validation requires Python without -O')
GAME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GAME))
sys.path.insert(0, str(GAME / 'queue'))
from combined.optimize import once
p = argparse.ArgumentParser()
p.add_argument('capture', type=Path)
a, rest = p.parse_known_args()
from journal.metadata import read_metadata
metadata_requests, metadata_rows = read_metadata(a.capture)
requests = [(label, bytes.fromhex(data)) for label, data in metadata_requests]
assert requests and requests[0][0] == 'browser-init'
assert all(label in ('browser-init', 'browser-reset-ack', 'browser-publish', 'browser-combined') and len(req) == 64 for label, req in requests)
from combined.model import Model
import struct
oracle = Model()
for sequence, (label, req) in enumerate(requests, 1):
    assert struct.unpack_from('<I', req, 4)[0] == {'browser-init':0, 'browser-reset-ack':2, 'browser-publish':1, 'browser-combined':4}[label]
    assert struct.unpack_from('<I', oracle.step(req, sequence), 8)[0] == 0
file = GAME / 'queue/verify.py'
s = once(file.read_text(), " cases=lambda epoch:pipeline_cases(epoch=epoch,combined=cfg['pipeline']=='combined')", ' cases=lambda epoch:browser_requests')
sys.argv = [str(file), str(a.capture), *rest]
exec(compile(s, str(file), 'exec'), dict(__name__='__main__', __file__=str(file), browser_requests=requests))
