#!/usr/bin/env python3
"""Seven independent sessions. No retries, service management or forced unload."""
import json,subprocess
from pathlib import Path
root=Path.cwd();game=root/'game/raycaster'
runs=[('base1','base','module50'),('validate','validate','module50'),('fast1','fast','module50'),('poll1','fast','module20'),('poll2','fast','module20'),('fast2','fast','module50'),('base2','base','module50')]
def payload(target):
 return root/('artifacts/transfer-20261011/kernel.bin' if target=='base' else 'target-'+target+'/session/kernel.bin')
def report(script,out,*args):
 with open(out,'w') as f:subprocess.run(['python3',str(script),*map(str,args)],stdout=f,check=True)
for name,target,module in runs:
 out=root/('live-'+name);ko=root/module/'dac960rtems.ko';image=payload(target)
 with open('live-'+name+'.log','w') as f:
  subprocess.run(['python3',str(game/'check_card.py'),'--payload',str(image),'--module',str(ko),'--output',str(out),'--command-profile','--cpu-profile'],stdout=f,stderr=subprocess.STDOUT,check=True)
 report(game/'verify_card.py',name+'-verified.json',out,'--payload',image,'--module',ko)
 report(game/'profile.py',name+'-profile.json',out/'phases.json')
 report(game/'transfer/profile.py',name+'-commands.json',out)
 report(game/'upload/verify_quiet.py',name+'-quiet.json',out)
 print(name,json.load(open(name+'-profile.json'))['phases']['render80'],flush=True)
