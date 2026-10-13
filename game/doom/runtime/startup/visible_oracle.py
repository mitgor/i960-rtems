#!/usr/bin/env python3
"""Accept two deterministic native visible frames and preserve their exact bytes."""
import argparse,hashlib,json,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('build',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
def fnv(b):
 h=2166136261
 for x in b:h=((h^x)*16777619)&0xffffffff
 return h
b=(a.build/'startup-0.bin').read_bytes();assert b==(a.build/'startup-4.bin').read_bytes() and len(b)==80+131072
w=struct.unpack_from('<20I',b);assert w[:3]==(0x454e4750,2,6291456) and w[5:7]==(2,1) and w[9:12]==(0,1,213)
assert w[15]==2 and w[16]+900000+4352<8*1048576
frames=b[80:];rows=[]
for i in range(2):
 f=frames[i*65536:(i+1)*65536];assert not any(f[64768:]);assert len(set(f[:64000]))>32
 rows.append(dict(pixel_sha256=hashlib.sha256(f[:64000]).hexdigest(),palette_sha256=hashlib.sha256(f[64000:64768]).hexdigest(),frame_fnv=fnv(f[:64000]),palette_fnv=fnv(f[64000:64768]),unique_indices=len(set(f[:64000]))))
# Early demo ticks may legitimately have identical pixels.
trace=(a.build/'startup-0.requests.bin').read_bytes();cp=(a.build/'startup-0.checkpoints.bin').read_bytes()
assert trace==(a.build/'startup-4.requests.bin').read_bytes() and cp==(a.build/'startup-4.checkpoints.bin').read_bytes() and len(cp)//32*2+5<512
checkpoints=list(struct.iter_unpack('<8I',cp));gametics=[v[6] for v in checkpoints if v[3]==80];assert gametics==[2,3]
assert [w[3],w[4]]==[rows[-1]['frame_fnv'],rows[-1]['palette_fnv']]
(a.output.parent/'visible-frames.bin').write_bytes(frames)
a.output.write_text(json.dumps(dict(visible=True,frame_count=2,gametics=gametics,exact_bytes_match=True,frame=1,frame_fnv=w[3],palette_fnv=w[4],frames=rows,frames_sha256=hashlib.sha256(frames).hexdigest(),request_count=len(trace)//8,peak_heap=w[16],checkpoint_count=len(cp)//32),indent=2)+'\n')
