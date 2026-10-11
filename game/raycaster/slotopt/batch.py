#!/usr/bin/env python3
"""Fail-stop measurement phases; no service control, retries, or forced unload."""
import argparse,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('phase',choices=['baseline','candidates','release','stress']);p.add_argument('--selected',choices=['hash','words']);a=p.parse_args()
if a.phase=='stress' and not a.selected:p.error('stress requires --selected from measured releases')
runs={'baseline':[('bench-byte','bench-byte','bench')],'candidates':[('bench-hash','bench-hash','bench'),('bench-words','bench-words','bench')],
 'release':[(n,t,'combined') for n,t in [('base1','base'),('hash1','hash'),('words1','words'),('words2','words'),('hash2','hash'),('base2','base')]],
 'stress':[('stress',a.selected,'stress')]}[a.phase]
root=Path.cwd();game=root/'game/raycaster'
for name,target,suite in runs:
 payload=root/('baseline.bin' if target=='base' else 'target-'+target+'/session/kernel.bin');module=root/'module/dac960rtems.ko';out=root/('live-'+name)
 with open(name+'.log','w') as f:subprocess.run(['python3',str(game/'slotopt/run.py'),'--suite',suite,'--payload',str(payload),'--module',str(module),'--output',str(out)],stdout=f,stderr=subprocess.STDOUT,check=True)
 with open(name+'-verified.json','w') as f:subprocess.run(['python3',str(game/'slotopt/run.py'),'--verify',str(out),'--payload',str(payload),'--module',str(module)],stdout=f,check=True)
 with open(name+'-quiet.json','w') as f:subprocess.run(['python3',str(game/'upload/verify_quiet.py'),str(out)],stdout=f,check=True)
 print(name,json.load(open(name+'-verified.json')),flush=True)
