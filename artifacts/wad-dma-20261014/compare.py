#!/usr/bin/env python3
"""Compare physical delivery with fixed menu inputs and native frame oracle."""
import argparse,json,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();r=a.root
captures={name:r/name for name in ('bulk','mailbox','bulk-repeat') if (r/name/'play-sessions.jsonl').exists()}
result={};all_requests={}
for name,d in captures.items():
 frames=[json.loads(s) for s in (d/'play-frames.jsonl').read_text().splitlines()];assert len(frames)==52
 rows=[]
 for i in range(1,53):
  b=(d/f'play-0-{i}.bin').read_bytes();n=(r/'native-levels'/f'frame-{i}.bin').read_bytes()
  diff=sum(x!=y for x,y in zip(b[:64000],n[:64000]));assert diff==(2 if i in (12,13) else 1 if i in (14,15) else 7),(name,i,diff)
  assert b[64000:]==n[64000:];rows.append(diff)
 requests={}
 for line in (d/'wad-journal.jsonl').read_text().splitlines():
  row=json.loads(line)
  if row['op']==3 and 'response' in row:
   w=struct.unpack_from('<8I',bytes.fromhex(row['response']),32)
   if w[0]==0x31424157 and w[2]==1:requests[w[1]]=w[4:7]
 assert len(requests)==5100
 all_requests[name]=sorted(requests.items())
 result[name]=dict(startup_seconds=frames[0]['engine_seconds'],upload_and_startup_seconds=frames[0]['seconds'],menu_confirm_to_new_frame_seconds=frames[17]['seconds']-frames[15]['seconds'],reload_requests=frames[17]['wad_requests']-frames[15]['wad_requests'],requests=len(requests),native_pixel_differences=rows,full_audit_pairs=len(json.loads((d/'snapshots.json').read_text())))
if 'mailbox' in captures:
  # Compare below after all source traces are read.
  pass
if 'mailbox' in captures and 'bulk-repeat' in captures:
 for i in range(1,53):assert (captures['mailbox']/f'play-0-{i}.bin').read_bytes()==(captures['bulk-repeat']/f'play-0-{i}.bin').read_bytes()
 assert all_requests['mailbox']==all_requests['bulk-repeat']
 b=result['mailbox'];f=result['bulk-repeat'];result['comparison']=dict(all_52_frames_byte_equal=True,startup_speedup=b['startup_seconds']/f['startup_seconds'],startup_reduction_percent=100*(1-f['startup_seconds']/b['startup_seconds']),reload_speedup=b['menu_confirm_to_new_frame_seconds']/f['menu_confirm_to_new_frame_seconds'])
print(json.dumps(result,indent=2))
