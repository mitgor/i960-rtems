#!/usr/bin/env python3
"""Quiet guarded transport with optional 20 us completion polling experiment."""
import argparse,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('quiet_builder',HERE.parent/'upload/build.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
def build(out,poll20=False,detail=True):
 base.build(out,True,detail)
 p=out/'dac960rtems.c';s=p.read_text()
 if poll20:
  # Only completion observation cadence changes. Keep IDB cadence and deadline.
  s=base.replace(s,'output & 1, 50, WAIT_US);','output & 1, 20, WAIT_US);')
 p.write_text(s)
 (out/'callback-transport.json').write_text(json.dumps(dict(completion_poll_us=20 if poll20 else 50,command_profile=detail),indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--poll20',action='store_true');p.add_argument('--coarse',action='store_true');a=p.parse_args();build(a.out,a.poll20,not a.coarse)
