#!/usr/bin/env python3
"""Copy a bounded evidence prefix without stopping the live game or touching PCI."""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess,tarfile
w=Path('/home/mit/i960-doom-play-20261013b');dest=w/'acceptance-prefix'
assert not dest.exists();dest.mkdir()
start=datetime.datetime.now(datetime.timezone.utc).isoformat();rows=[]
for src in sorted((w/'live').rglob('*')):
 if not src.is_file():continue
 rel=src.relative_to(w);out=dest/rel;out.parent.mkdir(parents=True,exist_ok=True)
 # Read at most the observed length; later appends remain in the live directory.
 n=src.stat().st_size
 with src.open('rb') as a,out.open('wb') as b:
  while n:
   data=a.read(min(n,1048576))
   if not data:break
   b.write(data);n-=len(data)
 rows.append(dict(path=str(rel),size=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest()))
for name in ('live.log','boot-id.txt','live-supervisor.pid','native-six.py'):
 shutil.copy2(w/name,dest/name)
shutil.copytree(w/'native-six',dest/'native-six')
frames=[]
for i in range(1,7):
 a=(w/f'native-six/frame-{i}.bin').read_bytes();b=(w/f'live/play-0-{i}.bin').read_bytes()
 differences=[dict(offset=j,native=x,card=y) for j,(x,y) in enumerate(zip(a,b)) if x!=y]
 frames.append(dict(frame=i,pixel_differences=sum(x['offset']<64000 for x in differences),palette_equal=a[64000:64768]==b[64000:64768],padding_equal=a[64768:]==b[64768:],differences=differences))
(dest/'native-comparison.json').write_text(json.dumps(frames,indent=2)+'\n')
(dest/'capture.json').write_text(json.dumps(dict(start=start,end=datetime.datetime.now(datetime.timezone.utc).isoformat(),kind='live evidence prefix; not atomic and not final shutdown',note='Open gzip streams may lack their footer; JSONL tails may be incomplete. Originals remain live. No global STOP/restoration claim.',files=rows),indent=2)+'\n')
(dest/'kernel.log').write_bytes(subprocess.check_output(['sudo','dmesg','--ctime']))
(dest/'owner.txt').write_bytes(subprocess.check_output(['sh','-c',"ps -p 2999,3001 -o pid,ppid,args; readlink /sys/bus/pci/devices/0000:37:09.1/driver"]))
with tarfile.open(w/'acceptance-prefix.tar.gz','w:gz') as t:t.add(dest,arcname=dest.name)
h=hashlib.sha256((w/'acceptance-prefix.tar.gz').read_bytes()).hexdigest();(w/'acceptance-prefix.sha256').write_text(h+'  acceptance-prefix.tar.gz\n');print(h)
