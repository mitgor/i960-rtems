#!/usr/bin/env python3
"""Sequential acceptance batch; abort on any failure, never auto-retry a session."""
import json,subprocess
from pathlib import Path
root=Path.cwd();game=root/'game/raycaster';payload=root/'artifacts/transfer-20261011/kernel.bin'
def report(script,out,*args):
 with open(out,'w') as f:subprocess.run(['python3',str(script),*map(str,args)],stdout=f,check=True)
for name,module in [('base1','module-base'),('fast1','module-quiet'),('fast2','module-quiet'),('base2','module-base'),('release','module-release')]:
 out=root/('live-'+name);ko=root/module/'dac960rtems.ko'
 args=['python3',str(game/'check_card.py'),'--payload',str(payload),'--module',str(ko),'--output',str(out)]
 if name!='release':args+=['--command-profile']
 with open('live-'+name+'.log','w') as f:subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,check=True)
 report(game/'verify_card.py',name+'-verified.json',out,'--payload',payload,'--module',ko)
 report(game/'profile.py',name+'-profile.json',out/'phases.json')
 if name!='release':report(game/'transfer/profile.py',name+'-commands.json',out)
 if not name.startswith('base'):report(game/'upload/verify_quiet.py',name+'-quiet.json',out)
 print(name,json.load(open(name+'-profile.json'))['phases']['render80'],flush=True)
report(game/'transfer/compare.py','comparison.json',root)
