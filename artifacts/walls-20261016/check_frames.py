#!/usr/bin/env python3
"""Compare all rendered pixels/palettes, and retain known native differences."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('captures',type=Path,nargs='+');p.add_argument('--native',type=Path,required=True);p.add_argument('--http-root',type=Path);a=p.parse_args()
base=a.captures[0];result={}
for out in a.captures:
 frames=[json.loads(x) for x in (out/'play-frames.jsonl').read_text().splitlines()];assert len(frames)==520
 for g in range(1,521):
  b=(out/f'play-0-{g}.bin').read_bytes();ref=(base/f'play-0-{g}.bin').read_bytes();assert b[:64768]==ref[:64768],(out,g,'render difference')
  if g<=52:
   n=(a.native/f'frame-{g}.bin').read_bytes();diff=[i for i in range(64768) if b[i]!=n[i]];assert diff==[29260,29261,29580,29581],(out,g,diff[:20])
 name=out.name.removeprefix('live-');http=[]
 if a.http_root:
  http=[json.loads(x) for x in (a.http_root/name/'http-observations.jsonl').read_text().splitlines()]
  for row in http:
   session,g=map(int,row['frame'].split('-'));assert hashlib.sha256((out/f'play-{session}-{g}.bin').read_bytes()).hexdigest()==row['payload_sha256']
 result[name]=dict(all_520_pixels_palettes_match=True,native_first_52_known_differences=[29260,29261,29580,29581],http_exact_frames=len(http))
print(json.dumps(result,indent=2))
