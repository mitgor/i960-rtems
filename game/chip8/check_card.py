#!/usr/bin/env python3
"""Explicit, exclusive card acceptance run; refuses an existing driver owner."""
import argparse
import json
from pathlib import Path
from host import Native, card_backend, decode, demo_rom, request

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--payload', type=Path, required=True)
p.add_argument('--module', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--steps', type=int, default=300)
a = p.parse_args()
if not 1 <= a.steps <= 10000:
    p.error('steps must be 1..10000')
reference = Native()
board = card_backend(a.payload, a.module, a.output)
try:
    reset = request(op=0, seed=19, rom=demo_rom())
    assert board.step(reset) == reference.step(reset)
    for i in range(a.steps):
        data = request(cycles=20, ticks=2, keys=1 << ([4, 6, 2, 8][i // 30 % 4]))
        actual = board.step(data)
        assert actual == reference.step(data), f'frame mismatch at {i}'
        assert decode(actual)['status'] == 0
    (a.output / 'chip8-validation.json').write_text(json.dumps(dict(
        matched_frames=a.steps, matched_reset=True, reply_bytes=304), indent=2) + '\n')
finally:
    print(json.dumps(board.close()))
