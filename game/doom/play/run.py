#!/usr/bin/env python3
"""Explicit RAM-only launch on the already qualified DAC960PG. No flash write."""
import argparse,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--port',type=int,default=8087);p.add_argument('--self-test',action='store_true');p.add_argument('--debug-audits',action='store_true');a=p.parse_args()
if os.geteuid():p.error('run with sudo on the Linux card host')
r=Path(__file__).resolve().parents[3];w=a.work.resolve()
subprocess.run(['python3',str(r/'rtems/residentnet/live.py'),'--payload',str(w/'residentnet/kernel.bin'),'--module',str(w/'residentnet-module/dac960auto.ko'),'--output',str(a.output.resolve()),'--resident-upload','--doom-heap','--doom-shared','--doom-runtime','--wad',str(w/'freedoom1.wad'),'--upload-concurrent','--owned-mib','12','--heap-shared','--queue-reclaim','--general-heap','--extra-ram','--fault-owner','--secondary-reset','--parallel','--ticks','540000','--rounds','1','--play-port',str(a.port),'--play-accept-frames','6' if a.self_test else '0','--audit-interval','3' if a.debug_audits else '60'],check=True)
