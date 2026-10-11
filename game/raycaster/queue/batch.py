#!/usr/bin/env python3
import subprocess,json
from pathlib import Path
root=Path.cwd();game=root/'game/raycaster'
for name,q in [('base1',False),('queue1',True),('queue2',True),('base2',False)]:
 payload=root/('target/session/kernel.bin' if q else 'baseline.bin');module=root/('module-queue' if q else 'module-base')/'dac960rtems.ko';out=root/('live-'+name)
 with open(name+'.log','w') as f:subprocess.run(['python3',str(game/'queue/live.py'),'--payload',str(payload),'--module',str(module),'--output',str(out),*(['--queue'] if q else [])],stdout=f,stderr=subprocess.STDOUT,check=True)
 with open(name+'-verified.json','w') as f:subprocess.run(['python3',str(game/'queue/verify.py'),str(out),'--payload',str(payload),'--module',str(module)],stdout=f,check=True)
 with open(name+'-quiet.json','w') as f:subprocess.run(['python3',str(game/'upload/verify_quiet.py'),str(out)],stdout=f,check=True)
 print(name,json.load(open(name+'-verified.json')),flush=True)
