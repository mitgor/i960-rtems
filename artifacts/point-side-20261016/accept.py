#!/usr/bin/env python3
"""Run predeclared A/B/B/A acceptance; archive/hash-check before each reboot."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REMOTE='/home/mit/i960-point-side-20261016'
HOST='mit@192.168.2.75'
LOCAL=Path('/tmp/i960-point-side-replay');LOCAL.mkdir(exist_ok=True)
def ssh(cmd,check=True):
 return subprocess.run(['ssh','-o','ConnectTimeout=5','-o','BatchMode=yes',HOST,cmd],text=True,capture_output=True,check=check)
def online():
 for i in range(20):
  x=ssh('cat /proc/sys/kernel/random/boot_id',False)
  if x.returncode==0:return x.stdout.strip()
  time.sleep(20)
 raise RuntimeError('PC did not return; no further action taken')
def fetch(remote,local):
 subprocess.run(['rsync','-a',HOST+':'+REMOTE+'/'+remote,str(local)],check=True)
parser=argparse.ArgumentParser();parser.add_argument('--runs',nargs='+',choices=('a1','b1','b2','a2'),default=['a1','b1','b2','a2']);args=parser.parse_args()
for name in args.runs:
 boot=online();out=ROOT/name;out.mkdir(exist_ok=True)
 (out/'boot-id.txt').write_text(boot+'\n')
 ssh('test ! -e /sys/bus/pci/devices/0000:37:09.1/driver')
 print(name,'starting',boot,flush=True)
 ssh('bash '+REMOTE+'/run.sh '+name)
 observer=subprocess.Popen(['python3',str(out/'observe_http.py')],stdout=(out/'http-observer.log').open('w'),stderr=subprocess.STDOUT)
 for i in range(120):
  time.sleep(15)
  state=ssh('ps -p $(cat '+REMOTE+'/'+name+'-supervisor.pid) -o args=',False)
  if state.returncode:break
 else:raise RuntimeError('test deadline; retained ownership untouched')
 if observer.poll() is None:
  try:observer.wait(timeout=10)
  except subprocess.TimeoutExpired:observer.terminate();observer.wait()
 print(name,'finished; replaying full audits',flush=True)
 build='build' if name.startswith('a') else 'build-fast'
 x=ssh('bash '+REMOTE+'/verify.sh '+name+' '+build)
 (out/'verification-command.log').write_text(x.stdout+x.stderr)
 ssh('bash '+REMOTE+'/archive.sh '+name)
 for suffix in ['-card.tar.gz','-card.tar.gz.sha256','-system.json','-frames.json','-wad.json','-profile.json','-drain-tamper.json','-frame-tamper.json']:
  fetch(name+suffix,out)
 archive=out/(name+'-card.tar.gz')
 assert hashlib.sha256(archive.read_bytes()).hexdigest()==(out/(name+'-card.tar.gz.sha256')).read_text().split()[0]
 fetch('live-'+name,LOCAL)
 print(name,'full replay passed, archive saved and hash verified',flush=True)
 if name!='a2':
  ssh('sudo reboot',False);time.sleep(20)
print('ALL FOUR SYSTEM/FRAME/WAD REPLAYS PASSED; run the separate image comparison; module retained',flush=True)
