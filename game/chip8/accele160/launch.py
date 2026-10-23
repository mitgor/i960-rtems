#!/usr/bin/env python3
"""Launch the pinned CHIP-8 card owner and its independent browser gateway."""
import argparse,json,hashlib,os,subprocess,sys,time
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,required=True)
 p.add_argument('action',choices=('start','stop','status','shutdown'),nargs='?',default='start')
 p.add_argument('--max-frames',type=int,default=0);p.add_argument('--paired-frames',choices=(4,32),type=int,default=4)
 p.add_argument('--restart-cycles',type=int,default=0);p.add_argument('--capture-all',action='store_true')
 a=p.parse_args();b=a.bundle.resolve();cfg=json.loads((b/'bundle.json').read_text())
 if cfg.get('application')!='chip8':raise ValueError('CHIP-8 identity')
 for name,digest in cfg['files'].items():
  f=(b/name).resolve()
  if not f.is_relative_to(b) or hashlib.sha256(f.read_bytes()).hexdigest()!=digest:raise ValueError('bundle identity: '+name)
 service='i960-chip8-stream.service'
 if a.action=='shutdown':subprocess.run(['systemctl','stop',service],check=False)
 command=[sys.executable,str(b/'project/game/doom/play/accele160/launch.py'),a.action,'--bundle',str(b),'--paired-frames',str(a.paired_frames),'--max-frames',str(a.max_frames),'--restart-cycles',str(a.restart_cycles)]
 if a.capture_all:command+=['--capture-all']
 subprocess.run(command,check=True)
 if a.action!='start':return
 deadline=time.monotonic()+120
 while True:
  try:
   state=json.loads(Path('/run/i960-chip8-control.json').read_text())
   pid=int(subprocess.check_output(['systemctl','show','-p','MainPID','--value','i960-chip8.service']))
   if pid>0 and state['pid']==pid and state['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip():break
  except (OSError,ValueError,KeyError):pass
  if time.monotonic()>deadline:raise RuntimeError('owner not ready; inspect i960-chip8.service; never unload retained resources')
  time.sleep(.5)
 if subprocess.run(['systemctl','is-active','--quiet',service]).returncode:
  vendor=Path('/home/mit/i960-doom-stream-20261018/vendor')
  subprocess.run(['systemd-run','--unit=i960-chip8-stream','--collect','--setenv=PYTHONPATH='+str(vendor),sys.executable,str(b/'project/game/chip8/stream/server.py'),'--backend','card','--bind','0.0.0.0','--port','8096','--journal',str(b.parent/'transport.jsonl')],check=True)
 print('CHIP-8: http://'+os.environ.get('I960_BROWSER_HOST','192.168.2.80')+':8096/ (Stop parks the guest; Start new game reuses RTEMS)')
if __name__=='__main__':main()
