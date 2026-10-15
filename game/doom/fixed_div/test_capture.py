#!/usr/bin/env python3
"""Check real profile trailers and reject schema tampering independently."""
import argparse,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'rtems/residentnet'))
from presentation_profile import decode
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args()
options=json.loads((a.capture/'presentation-options.json').read_text());assert options['fixed_div_profile']
rows=[json.loads(s) for s in (a.capture/'play-frames.jsonl').read_text().splitlines()]
for row in rows:
 g=row['frame'];raw=(a.capture/f'play-0-{g}.bin').read_bytes();d=decode(raw,g,options=options)
 assert d==row['profile']
 assert all(c or not t for c,t in zip(d['fixed_div']['counts'],d['fixed_div']['ticks']))
raw=(a.capture/'play-0-21.bin').read_bytes();rejected=0
for offset,value in [(65024,0),(65028,2),(65032,48),(65036,1-int(options['fast_fixed_div'])),(65040,0),(65044,0),(65052,1),(65532,1)]:
 b=bytearray(raw);struct.pack_into('<I',b,offset,value)
 try:decode(b,21,options=options)
 except AssertionError:rejected+=1
 else:raise AssertionError((offset,value))
print(json.dumps(dict(frames=len(rows),target_differential_checks=rows[-1]['profile']['fixed_div']['checks'],trailer_mutations_rejected=rejected)))
