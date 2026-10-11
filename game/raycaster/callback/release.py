#!/usr/bin/env python3
"""Coarse-profile acceptance of the lower-CPU 50 us candidate after the matrix."""
import subprocess
from pathlib import Path
root=Path.cwd();game=root/'game/raycaster';out=root/'live-release'
payload=root/'target-fast/session/kernel.bin';module=root/'module-release/dac960rtems.ko'
with open('live-release.log','w') as f:
 subprocess.run(['python3',str(game/'check_card.py'),'--payload',str(payload),'--module',str(module),'--output',str(out),'--cpu-profile'],stdout=f,stderr=subprocess.STDOUT,check=True)
for name,script,args in [('verified',game/'verify_card.py',[out,'--payload',payload,'--module',module]),('profile',game/'profile.py',[out/'phases.json']),('quiet',game/'upload/verify_quiet.py',[out])]:
 with open('release-'+name+'.json','w') as f:subprocess.run(['python3',str(script),*map(str,args)],stdout=f,check=True)
