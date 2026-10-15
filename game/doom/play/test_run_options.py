#!/usr/bin/env python3
"""Exercise CLI forwarding without opening hardware or spawning a runner."""
import runpy,sys
from pathlib import Path
from unittest.mock import patch
script=Path(__file__).with_name('run.py')
for args,want in [([], 'baseline'),(['--pipeline','--pipeline-test','--wad-dma','--pingpong'],'priority'),(['--pipeline','--pipeline-test','--wad-dma','--pingpong','--release-schedule','baseline'],'baseline'),(['--pipeline','--pipeline-test','--wad-dma','--pingpong','--wad-load-test','--frames','520','--release-schedule','abba'],'abba')]:
 calls=[]
 with patch.object(sys,'argv',[str(script),'--work','/tmp/build','--output','/tmp/output',*args]),patch('os.geteuid',return_value=0),patch('subprocess.run',side_effect=lambda c,**kw:calls.append(c)):
  runpy.run_path(str(script),run_name='__main__')
 assert len(calls)==1 and calls[0][calls[0].index('--release-schedule')+1]==want
 assert calls[0][calls[0].index('--play-frame-limit')+1]==('520' if want=='abba' else '0')
print('PASS default priority for Doom ping-pong, legacy baseline elsewhere, explicit baseline and long comparison forwarding')
