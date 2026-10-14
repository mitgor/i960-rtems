#!/usr/bin/env python3
"""Native renderer differences and retained-buffer identity, not completion proof."""
from pathlib import Path
import json,hashlib,sys
w=Path(sys.argv[1]);a=Path(__file__).resolve().parent;r=json.loads((a/'failed-frame-replay.json').read_text());rows=[]
for i in range(1,12):
 b=(w/f'live/play-0-{i}.bin').read_bytes();n=(w/f'native-28/frame-{i}.bin').read_bytes();assert b[64000:]==n[64000:];d=[j for j in range(64000) if b[j]!=n[j]]
 rows.append(dict(frame=i,differing_pixels=len(d),bounds=[min(j%320 for j in d),min(j//320 for j in d),max(j%320 for j in d),max(j//320 for j in d)] if d else None))
b=(w/'retained-frame-dma.bin').read_bytes();old=(a/'reference-mailbox-frame12.bin').read_bytes();assert b[4096:69632]==old and b[:4096]==b[69632:]==b'\xa5'*4096
r.update(native_comparison=rows,frame12_retained_bytes_match_previous_card=True,frame12_completion_proven=False,frame12_reference_sha256=hashlib.sha256(old).hexdigest())
print(json.dumps(r,indent=2))
