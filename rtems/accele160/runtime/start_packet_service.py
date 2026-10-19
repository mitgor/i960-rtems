#!/usr/bin/env python3
"""Start a frozen packet-DMA candidate after a confirmed host reset.
Does not reboot, force-unload, or adopt retained resources. Keeps PIO default
until an explicit matched DMA qualification succeeds.
"""
import argparse,json,subprocess,time,socket,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();root=a.root.resolve();bundle=root/'bundle';src=bundle/'project/rtems/accele160/runtime'
sys.path.insert(0,str(src));from client import Client
from service import Service
s=Service()
def run(*args):subprocess.run(args,check=True)
for name in ('dma_frames','admit_command','reserve_command'):
 if Path('/sys/module',name).exists():raise SystemExit('retained '+name+': reset required; no adoption')
run('python3',str(bundle/'project/game/doom/play/accele160/launch.py'),'start','--bundle',str(bundle),'--max-frames','64','--paired-frames','32','--keyboard-mode','fifo','--capture-all','--quit-game','0','--restart-cycles','0')
for _ in range(900):
 try:text=s.console('apps')
 except OSError:text=''
 if 'idle=1' in text and 'frames=64' in text and Path('/run/i960-rtems-runtime.sock').exists():break
 time.sleep(1)
else:raise SystemExit('baseline not ready: retain owner and inspect journal')
(root/'baseline-apps.txt').write_text(text)
c=Client('/run/i960-rtems-runtime.sock');before=c.call(7)
assert not before['reservation'] and not before['poisoned']
loaded=c.upload(bundle/'network');assert loaded['started'] and not loaded['poisoned']
(root/'initial-upload.json').write_text(json.dumps(dict(before=before,loaded=loaded),indent=2)+'\n')
run('python3',str(src/'start_broker.py'),'--root',str(root))
print('Fresh kernel, 64-frame baseline and combined module ready; PIO default. Run raw benchmark before starting TUN.')
