#!/usr/bin/env python3
import json
from pathlib import Path
import argparse
p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();out={}
for name in ('bulk','mailbox'):
 d=a.directory/name
 if not (d/'play-frames.jsonl').exists():continue
 frames=[json.loads(s) for s in (d/'play-frames.jsonl').read_text().splitlines()]
 gaps=[dict(frame=f['frame'],seconds=f['seconds']-prev['seconds'],requests=f['wad_requests']-prev['wad_requests']) for prev,f in zip(frames,frames[1:])]
 out[name]=dict(first_frame_seconds=frames[0]['engine_seconds'],first_frame_requests=frames[0]['wad_requests'],total_requests=frames[-1]['wad_requests'],frame_count=len(frames),menu_reload_delivery_seconds=frames[17]['seconds']-frames[15]['seconds'] if len(frames)>=18 else None,level_transition_candidates=[g for g in gaps if g['frame']>=16 and g['requests']>=20],frame_gaps=gaps)
print(json.dumps(out,indent=2))
