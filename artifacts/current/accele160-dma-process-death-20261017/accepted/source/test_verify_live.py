#!/usr/bin/env python3
"""Reject altered process-death, ownership, flash and DMA captures."""
import importlib.util,json,shutil,sys,tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('death_verify',
    Path(__file__).with_name('verify_live.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

def flip(path,offset):
    b=bytearray(path.read_bytes());b[offset]^=1;path.write_bytes(b)

def main(root):
    baseline=v.verify(root)
    cases=(
      ('flash','accepted/live/post-flash-1/data.bin',0),
      ('image','accepted/image/image.bin',0),
      ('source','accepted/source/recover.py',0),
      ('death-marker','accepted/live/attempt-0/death-intent.json',0),
      ('death-observation','accepted/live/attempt-1/death-observation.json',0),
      ('held-page','accepted/live/attempt-0/halt/held-page.bin',0xa50),
      ('held-owner','accepted/live/attempt-0/halt/held-owner.bin',0x2a0),
      ('grant-owner','accepted/live/attempt-1/owner-after.bin',0x2a0),
      ('stop-active','accepted/live/attempt-0/halt/irq-stack-after.bin',3072+82*4),
      ('resume-tick','accepted/live/attempt-1/halt/irq-stack-after.bin',3072+85*4),
      ('hold-stability','accepted/live/attempt-0/halt/irq-stack-after.bin',3072+91*4),
      ('channel-idle','accepted/live/attempt-1/halt/irq-stack-after.bin',3072+44*4),
      ('host-payload','accepted/live/attempt-1/halt/dma-data.bin',0),
      ('worker-done','accepted/live/attempt-0/halt/irq-stack-after.bin',3072+34*4),
      ('prior-state','accepted/live/attempt-1/preflight.json',0))
    caught=[]
    for name,rel,offset in cases:
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)/'accele160-dma-process-death-20261017'
            shutil.copytree(root,dst)
            for previous in ('accele160-dma-timeout-20261017',
                             'accele160-dma-suspend-20261017'):
                shutil.copytree(root.parent/previous,Path(td)/previous)
            flip(dst/rel,offset)
            try:v.verify(dst)
            except (ValueError,AssertionError,KeyError,UnicodeDecodeError,
                    json.JSONDecodeError):caught.append(name)
            else:raise AssertionError('tamper accepted: '+name)
    print(json.dumps(dict(replay=baseline,tamper_rejected=caught),indent=2))

if __name__=='__main__':main(Path(sys.argv[1]))
