#!/usr/bin/env python3
"""Exact old/new card payload comparison, excluding only explicit profile bytes."""
import json
from pathlib import Path
w=Path(__file__).resolve().parent
rows=[]
for g in range(17,41):
 old=(w/'prior-low'/f'play-0-{g}.bin').read_bytes()
 new=(w/'live'/f'play-0-{g}.bin').read_bytes()
 assert old[:64768]==new[:64768],g
 rows.append(g)
print(json.dumps(dict(exact_prior_card_frames=rows,pixel_and_palette_bytes_per_frame=64768)))
