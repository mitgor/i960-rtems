#!/usr/bin/env python3
"""Read-only retention audit after the diagnostic owner process has exited."""
import argparse,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('session',type=Path);a=p.parse_args()
run=a.session/'run';result=json.loads((run/'result.json').read_text())
assert result['terminal']['mode'] in (8,9,10)
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==result['boot_id']
u=subprocess.run(['systemctl','is-active','i960-doom.service'],capture_output=True,text=True)
assert u.returncode!=0 and u.stdout.strip() in ('inactive','failed','unknown')
def fields(p):return dict(v.split('=',1) for v in p.read_text().split())
d=Path('/sys/kernel/debug');admit=fields(d/'accele-ram-admit/status');pins=fields(d/'accele-frame-dma/status')
assert admit['done']=='0' and admit['released']=='0' and admit['submitted']=='1'
assert pins==result['terminal']['pin'] and pins['retained']=='1' and pins['guard_changes']=='0'
frames={}
for slot in (0,1):
    current=(d/f'accele-frame-dma/frame{slot}.bin').read_bytes()
    assert current==(run/f'terminal/frame{slot}.bin').read_bytes()
    frames[str(slot)]=hashlib.sha256(current).hexdigest()
r=dict(boot_id=result['boot_id'],owner_unit=u.stdout.strip(),admission=admit,pin=pins,frame_sha256=frames)
(run/'post-owner-exit.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
