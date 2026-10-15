#!/usr/bin/env python3
"""Keep browser/host key values aligned with the pinned DoomGeneric controls."""
import re,tarfile
from pathlib import Path
r=Path(__file__).resolve().parents[3]
with tarfile.open(r/'artifacts/doom-m1-20261011/doomgeneric-source.tar.gz') as t:
 keys=next(m for m in t.getmembers() if m.name.endswith('/doomkeys.h'));text=t.extractfile(keys).read().decode()
for name,value in [('KEY_FIRE',163),('KEY_USE',162),('KEY_UPARROW',173),('KEY_RIGHTARROW',174)]:
 assert int(re.search(r'#define\s+'+name+r'\s+(0x[0-9a-f]+|[0-9]+)',text)[1],0)==value
assert re.search(r'#define\s+KEY_F5\s+\(0x80\+0x3f\)',text)
page=(r/'game/doom/play/index.html').read_text()
for pair in ('F5:191','ControlLeft:163','ControlRight:163','Space:163','KeyE:162','KeyY:121','KeyN:110','Digit1:49','Digit7:55'):assert pair in page,pair
for src in ('rtems/residentnet/play_client.py','game/doom/play/input_bridge.py'):
 s=(r/src).read_text();assert '173,175,172,174,163,162,182,191,13,27,9,121,110,49,50,51,52,53,54,55' in s
print('PASS pinned DoomGeneric fire/use and browser/menu/weapon key mappings')
