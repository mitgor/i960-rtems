#!/usr/bin/env python3
"""One fail-stop A/B/B/A batch; service control and ownership stay external."""
import json,subprocess
from pathlib import Path
root=Path.cwd();game=root/'game/raycaster'
for name,mode in [('separate1','separate'),('combined1','combined'),('combined2','combined'),('separate2','separate')]:
 payload=root/('target/session/kernel.bin' if mode=='combined' else 'baseline.bin');module=root/'module/dac960rtems.ko';out=root/('live-'+name)
 with open(name+'.log','w') as f:subprocess.run(['python3',str(game/'queue/live.py'),'--payload',str(payload),'--module',str(module),'--output',str(out),'--queue','--pipeline',mode],stdout=f,stderr=subprocess.STDOUT,check=True)
 with open(name+'-verified.json','w') as f:subprocess.run(['python3',str(game/'queue/verify.py'),str(out),'--payload',str(payload),'--module',str(module)],stdout=f,check=True)
 with open(name+'-quiet.json','w') as f:subprocess.run(['python3',str(game/'upload/verify_quiet.py'),str(out)],stdout=f,check=True)
 print(name,json.load(open(name+'-verified.json')),flush=True)
