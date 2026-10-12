"""Closed relocation proof: hostile admission cases, then two real entries."""
import hashlib,json,time,zlib
from pathlib import Path

def exercise(u,root):
 root=Path(root);m=json.loads((root/'manifest.json').read_text());b=(root/'template.bin').read_bytes();rows=[]
 assert hashlib.sha256(b).hexdigest()==m['sha256']
 u.command(13,expected=1) # No image.
 for mode in ('entry','code','data','valid'):
  blob=bytearray(b);entry=m['entry']
  if mode=='entry':entry+=4
  if mode=='code':blob[0]^=1
  if mode=='data':blob[m['seed_offset']]^=1
  segments=[(s['offset'],s['file_bytes'],s['memory_bytes'],s['flags'],zlib.crc32(blob[s['offset']:s['offset']+s['file_bytes']])) for s in m['sections']]
  u.begin(segments,entry);u.command(13,expected=1)
  for i,s in enumerate(m['sections']):
   if s['file_bytes']:u.write(i,blob[s['offset']:s['offset']+s['file_bytes']])
  u.prepare();base_offset=u.command(14)[5]
  for _ in range(2 if mode=='valid' else 1):
   start=time.monotonic();w=u.command(13,expected=0 if mode=='valid' else 1 if mode=='entry' else 2)
   if mode=='valid':assert w[5]==(5*33)^0x49393630 and w[4]==3
   rows.append(dict(mode=mode,rc=w[2],value=w[5],seconds=time.monotonic()-start,handle=w[15],base_offset=base_offset,base=0xc02d0040+base_offset))
  u.command(5);assert u.command(6)[5]==1
 (u.out/'relocate-results.json').write_text(json.dumps(dict(manifest=m,runs=rows),indent=2)+'\n')
 (u.out/'relocate-template.bin').write_bytes(b)
