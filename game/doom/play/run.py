#!/usr/bin/env python3
"""Explicit RAM-only launch on the already qualified DAC960PG. No flash write."""
import argparse,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--port',type=int,default=8087);p.add_argument('--dma-test',action='store_true');p.add_argument('--pipeline',action='store_true');p.add_argument('--pipeline-test',action='store_true');p.add_argument('--no-crc',action='store_true');p.add_argument('--bulk',action='store_true');p.add_argument('--bulk-test',action='store_true');p.add_argument('--self-test',action='store_true');p.add_argument('--debug-audits',action='store_true');a=p.parse_args()
if a.pipeline_test and a.no_crc:p.error('pipeline-test selects both CRC modes itself')
if (a.pipeline_test or a.no_crc) and not a.pipeline:p.error('pipeline-test and no-crc require pipeline')
if a.pipeline and (a.dma_test or a.bulk or a.bulk_test or a.self_test):p.error('pipeline is a separate mode')
if a.dma_test and (a.bulk or a.bulk_test or a.self_test):p.error('--dma-test is a separate bounded acceptance run')
if a.bulk_test and a.self_test:p.error('--bulk-test and --self-test are separate acceptance runs')
if os.geteuid():p.error('run with sudo on the Linux card host')
r=Path(__file__).resolve().parents[3];w=a.work.resolve()
subprocess.run(['python3',str(r/'rtems/residentnet/live.py'),'--payload',str(w/'residentnet/kernel.bin'),'--module',str(w/'residentnet-module/dac960auto.ko'),'--output',str(a.output.resolve()),'--resident-upload','--doom-heap','--doom-shared','--doom-runtime','--wad',str(w/'freedoom1.wad'),'--upload-concurrent','--owned-mib','12','--heap-shared','--queue-reclaim','--general-heap','--extra-ram','--fault-owner','--secondary-reset','--parallel','--ticks','540000','--rounds','1','--play-port',str(a.port),'--play-accept-frames','6' if a.self_test else '0','--audit-interval','3' if a.debug_audits else '60',*(['--play-bulk'] if a.bulk else []),*(['--play-bulk-test'] if a.bulk_test else []),*(['--play-dma-test'] if a.dma_test else []),*(['--play-pipeline'] if a.pipeline else []),*(['--play-pipeline-test'] if a.pipeline_test else []),*(['--play-no-crc'] if a.no_crc else [])],check=True)
