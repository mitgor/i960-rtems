#!/usr/bin/env python3
"""Negative evidence only. This is never a substitute for full acceptance."""
import hashlib,json,struct,sys,zlib
from pathlib import Path
w=Path(sys.argv[1]);p=w/'live';frames=[json.loads(x) for x in (p/'play-frames.jsonl').read_text().splitlines()];reports=[json.loads(x) for x in (p/'frame-dma-results.jsonl').read_text().splitlines()]
assert len(frames)==len(reports)==7 and (p/'error.txt').exists()
for g,(f,r) in enumerate(zip(frames,reports),1):
 b=(p/f'play-0-{g}.bin').read_bytes();guarded=(p/f'frame-dma-{g:03}.bin').read_bytes();h=r['report']
 assert f['frame']==r['frame']==g and hashlib.sha256(b).hexdigest()==f['sha256']
 assert guarded==b'\xa5'*4096+b+b'\xa5'*4096 and h[2]==g and not h[13]
 assert h[14]==int(not f['crc'])
 assert (h[5]==h[6]==zlib.crc32(b)) if f['crc'] else h[5]==h[6]==0
 assert (p/f'play-0-{g}.dfb').read_bytes()==struct.pack('<8I',0x31424644,1,0,g,320,200,65536,int(f['crc']))+b
assert (w/'retained-frame-dma.bin').read_bytes()==b'\xa5'*73728
fault=json.loads((w/'retained-fault-decoded.json').read_text());assert fault['terminal_identity_verified'] and fault['dma']['generation']==8 and fault['dma']['phase']==1 and fault['dma']['error']==0
assert fault['heap']['error']==0 and fault['isolation']['scsi_verified']==1
assert not (p/'play-sessions.jsonl').exists()
print(json.dumps(dict(accepted=False,completed_prefix_frames=7,pending_frame=8,destination_untouched=True,full_acceptance_unavailable=True),indent=2))
