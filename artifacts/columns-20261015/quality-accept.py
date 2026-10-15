#!/usr/bin/env python3
"""Bounded runtime detail acceptance, separately from the fixed-quality A/B test."""
import hashlib,json,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parent;out=root/'quality';out.mkdir(exist_ok=True)
remote='/home/mit/i960-columns-20261015';host='mit@192.168.2.75'
def ssh(cmd,check=True):return subprocess.run(['ssh','-o','ConnectTimeout=5',host,cmd],capture_output=True,text=True,check=check)
for i in range(20):
 s=ssh('cat /proc/sys/kernel/random/boot_id',False)
 if not s.returncode:break
 time.sleep(20)
else:raise RuntimeError('Host did not return; no further action')
(out/'boot-id.txt').write_text(s.stdout)
ssh('test ! -e /sys/bus/pci/devices/0000:37:09.1/driver')
ssh('cd '+remote+'; sudo nohup python3 project/game/doom/play/run.py --work '+remote+'/build-runtime --output '+remote+'/live-quality --pipeline --pipeline-test --wad-dma --wad-ring --pingpong --debug-audits --wad-load-test --port 8087 --frames 100 --release-schedule priority > live-quality.log 2>&1 < /dev/null & echo $! > quality-supervisor.pid')
print('Runtime quality test started',flush=True)
observer=subprocess.Popen(['python3',str(out/'observe_http.py')],stdout=(out/'http-observer.log').open('w'),stderr=subprocess.STDOUT)
for i in range(100):
 time.sleep(15)
 if ssh('ps -p $(cat '+remote+'/quality-supervisor.pid) -o args=',False).returncode:break
else:raise RuntimeError('Test deadline; ownership retained')
if observer.poll() is None:
 try:observer.wait(timeout=10)
 except subprocess.TimeoutExpired:observer.terminate();observer.wait()
x=ssh('bash '+remote+'/verify.sh quality build-runtime');(out/'verification-command.log').write_text(x.stdout+x.stderr)
ssh('bash '+remote+'/archive.sh quality')
for suffix in ['-card.tar.gz','-card.tar.gz.sha256','-system.json','-frames.json','-wad.json','-profile.json','-drain-tamper.json','-frame-tamper.json']:
 subprocess.run(['rsync','-a',host+':'+remote+'/quality'+suffix,str(out)],check=True)
assert hashlib.sha256((out/'quality-card.tar.gz').read_bytes()).hexdigest()==(out/'quality-card.tar.gz.sha256').read_text().split()[0]
subprocess.run(['rsync','-a',host+':'+remote+'/live-quality','/tmp/i960-columns-replay/'],check=True)
print('Quality test replay passed; archive saved and hash verified; module retained',flush=True)
