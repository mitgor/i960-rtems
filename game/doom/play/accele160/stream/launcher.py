#!/usr/bin/env python3
"""Start browser streaming alongside the original exclusive Doom launcher.

The original launcher remains the only card owner. This helper neither adopts
retained resources nor changes its audited inputs. Stop parks only the game.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request


def main():
    parser=argparse.ArgumentParser(description=__doc__,add_help=False,allow_abbrev=False)
    parser.add_argument('--gateway-root',type=Path,required=True)
    parser.add_argument('--owner-launcher',type=Path,required=True)
    parser.add_argument('--stream-port',type=int,default=8088)
    args, forwarded=parser.parse_known_args()
    if not 1024<=args.stream_port<=65535:raise ValueError('stream port')
    root=args.gateway_root.resolve()
    for name,digest in json.loads((root/'gateway-manifest.json').read_text()).items():
        path=(root/name).resolve()
        if not path.is_relative_to(root) or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise RuntimeError('gateway identity: '+name)
    action=next((x for x in forwarded if x in ('start','run','status','stop','shutdown')),'start')
    if action=='shutdown':
        subprocess.run(['sudo','-n','systemctl','stop','i960-doom-stream.service'],check=True)
    result=subprocess.run([str(args.owner_launcher),*forwarded])
    if result.returncode or '--help' in forwarded:return result.returncode
    if action=='status':
        subprocess.run(['systemctl','status','i960-doom-stream.service','--no-pager'],check=False)
    if action!='start':return 0
    control=Path('/run/i960-doom-control.json')
    deadline=time.monotonic()+90
    while True:
        try:
            # The control file is owner-only; read through sudo without printing
            # credentials. A service which exits during startup cannot be adopted.
            state=json.loads(subprocess.check_output(['sudo','-n','cat',str(control)],stderr=subprocess.DEVNULL))
            boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
            main_pid=int(subprocess.check_output(['systemctl','show','-p','MainPID','--value','i960-doom.service']))
            if state['boot_id']==boot and state['pid']==main_pid and main_pid>0:break
        except (OSError,ValueError,KeyError,subprocess.CalledProcessError):pass
        if time.monotonic()>deadline:raise RuntimeError('owner not ready; inspect i960-doom.service, do not unload resources')
        time.sleep(.5)
    if state['port']==args.stream_port:raise ValueError('stream port conflicts with owner HTTP port')
    active=subprocess.run(['systemctl','is-active','--quiet','i960-doom-stream.service']).returncode==0
    if active:
        command=subprocess.check_output(['systemctl','show','-p','ExecStart','--value','i960-doom-stream.service'],text=True)
        if f'--port {args.stream_port} ' not in command:
            raise RuntimeError('stream service uses another port; stop only i960-doom-stream before changing its port')
    else:
        subprocess.run(['sudo','-n','systemctl','reset-failed','i960-doom-stream.service'],capture_output=True)
        subprocess.run(['sudo','-n','systemd-run','--unit=i960-doom-stream','--collect',
            '--setenv=PYTHONPATH='+str(root/'vendor'),'/usr/bin/python3',str(root/'source/gateway.py'),
            '--port',str(args.stream_port),'--journal',str(root/'transport.jsonl')],check=True)
    ready_deadline=time.monotonic()+8
    while True:
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{args.stream_port}/status',timeout=1) as response:
                if isinstance(json.load(response),dict):break
        except (OSError,ValueError):pass
        if time.monotonic()>ready_deadline:
            raise RuntimeError('stream gateway not ready; owner is unchanged, inspect i960-doom-stream.service')
        time.sleep(.2)
    browser_host=os.environ.get('I960_BROWSER_HOST','192.168.2.80')
    print(f'Persistent input and pushed frames: http://{browser_host}:{args.stream_port}/',flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
