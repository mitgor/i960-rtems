#!/usr/bin/env python3
"""Report every image discrepancy; do not convert the strict oracle into a pass."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('captures',type=Path);p.add_argument('--native',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parent
base=a.captures/'live-a1';rows={}
for name in ('a1','b1','b2','a2'):
 out=a.captures/('live-'+name);diffs=[];native_diffs=[]
 for g in range(1,521):
  b=(out/f'play-0-{g}.bin').read_bytes();ref=(base/f'play-0-{g}.bin').read_bytes()
  if b[:64768]!=ref[:64768]:diffs.append(g)
  if g<=52:
   n=(a.native/f'frame-{g}.bin').read_bytes();d=[i for i in range(64768) if b[i]!=n[i]]
   assert d==[29260,29261,29580,29581],(name,g,d[:20])
 http=[json.loads(x) for x in (root/name/'http-observations.jsonl').read_text().splitlines()]
 for row in http:
  s,g=map(int,row['frame'].split('-'));assert hashlib.sha256((out/f'play-{s}-{g}.bin').read_bytes()).hexdigest()==row['payload_sha256']
 rows[name]=dict(pixel_palette_mismatch_frames=diffs,all_images_equal=not diffs,measurement_window_images_equal=not any(100<=g<=499 for g in diffs),http_exact_frames=len(http),native_first_52_known_differences=[29260,29261,29580,29581])
print(json.dumps(dict(strict_all_run_image_acceptance=all(x['all_images_equal'] for x in rows.values()),runs=rows),indent=2))
