#!/usr/bin/env python3
"""Start a pinned AcceleRAID Doom bundle; no firmware programming commands."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def verify(bundle):
    cfg=json.loads((bundle/'bundle.json').read_text())
    if cfg['schema']!=1 or cfg['card_profile']!='accele160':
        raise ValueError('unsupported bundle/card profile')
    for name,digest in cfg['files'].items():
        path=(bundle/name).resolve()
        if not path.is_relative_to(bundle) or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError('bundle file identity: '+name)
    return cfg


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('start','run','status','stop'),nargs='?',default='start')
    p.add_argument('--bundle',type=Path,required=True)
    p.add_argument('--port',type=int,default=8087)
    p.add_argument('--max-frames',type=int,default=0)
    p.add_argument('--capture-all',action='store_true')
    p.add_argument('--disconnect-seconds',type=float,default=300)
    a=p.parse_args();bundle=a.bundle.resolve()
    if a.action=='status':
        return subprocess.run(['systemctl','status','i960-doom.service','--no-pager']).returncode
    if a.action=='stop':
        return subprocess.run(['systemctl','stop','i960-doom.service']).returncode
    if not 1024<=a.port<=65535 or a.max_frames<0 or a.disconnect_seconds<5:
        p.error('invalid session bounds')
    cfg=verify(bundle)
    sys.path.insert(0,str(bundle/'project/rtems/transport'))
    from card_select import select
    card=select(cfg['bdf'],'accele160')
    if card['driver'] not in (None,'myrsread'):
        raise RuntimeError('new card already owned by '+card['driver'])
    if select(cfg['old_bdf'],'dac960pg')['driver'] is not None:
        raise RuntimeError('old card must remain unbound')
    if a.action=='start':
        active=subprocess.run(['systemctl','is-active','--quiet','i960-doom.service']).returncode==0
        if active:
            print(f'Doom is already running. Open http://192.168.2.75:{a.port}/');return 0
    for name in ('dma_frames','admit_command','reserve_command','copy_command','digest_command','release_command'):
        if Path('/sys/module',name).exists():
            raise RuntimeError('Previous card resources are retained. Reset/power-cycle the PC before starting again; never force-unload.')
    if card['driver'] is None and Path('/sys/module/myrsread').exists():
        raise RuntimeError('myrsread is loaded but card initialization failed; power-cycle before retrying')
    if a.action=='start':
        subprocess.run(['systemctl','reset-failed','i960-doom.service'],check=False,capture_output=True)
        command=['systemd-run','--unit=i960-doom','--collect',
                 '--property=TimeoutStopSec=90','--property=SendSIGKILL=no',
                 '--setenv=PYTHONUNBUFFERED=1',sys.executable,str(Path(__file__).resolve()),
                 'run','--bundle',str(bundle),'--port',str(a.port),
                 '--max-frames',str(a.max_frames),'--disconnect-seconds',str(a.disconnect_seconds)]
        if a.capture_all:command+=['--capture-all']
        subprocess.run(command,check=True)
        print(f'Doom is starting. Open http://192.168.2.75:{a.port}/')
        print('Startup takes a few minutes. Logs: sudo journalctl -fu i960-doom')
        return 0
    lock=open('/run/lock/i960-doom-start.lock','w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if card['driver'] is None:
        subprocess.run(['modprobe','raid_class'],check=True)
        subprocess.run(['insmod',str(bundle/'inputs/myrsread.ko'),'read_bdf='+cfg['bdf']],check=True)
    select(cfg['bdf'],'accele160',driver='myrsread')
    session=bundle.parent/'sessions'/time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())
    session.mkdir(parents=True,exist_ok=False)
    (bundle.parent/'latest-session.txt').write_text(str(session)+'\n')
    project=bundle/'project'
    for number in (0,1):
        subprocess.run([sys.executable,str(project/'host/accele160/readimage/read_image.py'),
                        '--bdf',cfg['bdf'],'--module',str(bundle/'inputs/rawreader.ko'),
                        '--selector','9','--length','1048576','--out',str(session/f'pre-{number}')],check=True)
    command=[sys.executable,str(project/'rtems/accele160/doom_dma/run_bridge.py'),
             '--persistent','--port',str(a.port),'--card-fnv','off',
             '--max-frames',str(a.max_frames),'--disconnect-seconds',str(a.disconnect_seconds),
             '--fps-manifest',str(project/'rtems/accele160/doom_dma/persistent-manifest.json'),
             '--startup-oracle',str(bundle/'inputs/native-requests.bin'),
             '--engine-manifest',str(bundle/'engine/manifest.json'),
             '--dma-module',str(bundle/'inputs/dma_frames.ko'),
             '--kernel',str(bundle/'kernel/kernel.bin'),'--image',str(bundle/'kernel/image.bin'),
             '--handler',str(bundle/'inputs/handler.bin'),'--firmware',str(bundle/'inputs/candidate.bin'),
             '--template',str(bundle/'engine/template.bin'),'--relocations',str(bundle/'engine/relocations.bin'),
             '--wad',str(bundle/'inputs/freedoom1.wad'),
             '--readback0',str(session/'pre-0'),'--readback1',str(session/'pre-1'),'--out',str(session/'run')]
    for name in ('reserve','release','copy','digest','admit'):
        command+=['--'+name+'-module',str(bundle/'inputs'/(name+'_command.ko'))]
    if a.capture_all:command+=['--capture-all']
    os.execv(sys.executable,command)


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError,ValueError,OSError) as e:
        print('Doom:',e,file=sys.stderr)
        raise SystemExit(1)
