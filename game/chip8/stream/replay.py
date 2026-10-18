#!/usr/bin/env python3
"""Read a captured tar without extraction; replay compact DMA frames and guards."""
import argparse,tarfile,json,hashlib,struct
from oracle import Oracle
from host import demo_rom
p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive');a=p.parse_args()
with tarfile.open(a.archive) as tar:
 members={m.name:m for m in tar.getmembers() if m.isfile()}
 read=lambda name:tar.extractfile(members[name]).read()
 count=0;games=0
 for journal in sorted(n for n in members if n.endswith('/live-frame-receipts.jsonl')):
  base=journal.rsplit('/',1)[0];o=Oracle(demo_rom());keys=[json.loads(line) for line in read(base+'/keyboard-receipts.jsonl').splitlines()];keypos=0
  for line in read(journal).splitlines():
   receipt=json.loads(line);n=receipt['generation'];local=receipt['local_frame']
   # Commit key events in host publication order before replay; card trace
   # selects only events it has actually consumed.
   wanted=receipt['profile']['input_seen']
   while o.base+len(o.events)<wanted:
    while keypos<len(keys) and keys[keypos]['op']!='submit':keypos+=1
    if keypos==len(keys):raise ValueError('missing committed key batch')
    o.submit(keys[keypos]['events']);keypos+=1
   raw=read(base+f'/live-frames/frame-{n:04d}.bin')
   assert len(raw)==512 and hashlib.sha256(raw).hexdigest()==receipt['sha256']
   o.check(raw)
   capture=read(base+f'/dma-frame-{n:04d}.bin')
   assert len(capture)==12288 and capture[:4096]==b'\xa5'*4096 and capture[4640:]==b'\xa5'*(12288-4640)
   assert capture[4096:4608]==raw
   marker=struct.unpack('<8I',capture[4608:4640])
   assert marker==(0x31505044,0x161610e1,n,receipt['slot'],512,receipt['source'],receipt['card_tick'],(~n)&0xffffffff)
   fnv=2166136261
   for byte in raw:fnv=((fnv^byte)*16777619)&0xffffffff
   assert fnv==int(receipt['fnv'],16)
   count+=1
  games+=1
 print(json.dumps(dict(games=games,frames=count,native_replay=True,compact_guards=True,sha256=True),indent=2))
