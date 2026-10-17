#!/usr/bin/env python3
"""Reject altered flash, host deadline, release denial and DMA ownership."""
import importlib.util,json,shutil,sys,tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('chain_verify',Path(__file__).with_name('verify_live.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

def flip(path,offset):
    b=bytearray(path.read_bytes());b[offset]^=1;path.write_bytes(b)

def main(root):
    baseline=v.verify(root)
    cases=(
      ('flash','accepted/live/post-flash-1/data.bin',0),
      ('image','accepted/image/image.bin',0),
      ('prior-channel','accepted/prior/attempt-1/halt/irq-stack-after.bin',3072+44*4),
      ('owner','accepted/live/attempt-0/owner-after.bin',0x2a0),
      ('dma-active-stop','accepted/live/attempt-0/halt/irq-stack-after.bin',3072+82*4),
      ('suspend-tick','accepted/live/attempt-1/halt/irq-stack-after.bin',3072+84*4),
      ('hold-stability','accepted/live/attempt-1/halt/irq-stack-after.bin',3072+91*4),
      ('held-page','accepted/live/attempt-1/halt/held-page.bin',0xa50),
      ('timeout-page','accepted/live/attempt-1/halt/host-timeout-page.bin',0xa50),
      ('release-denied','accepted/live/attempt-1/halt/release-denied.json',0),
      ('held-owner','accepted/live/attempt-0/halt/held-owner.bin',0x2a0),
      ('resume-ccr','accepted/live/attempt-1/halt/irq-stack-after.bin',3072+87*4),
      ('final-descriptor','accepted/live/attempt-1/halt/irq-stack-after.bin',3072+45*4),
      ('host-payload','accepted/live/attempt-0/halt/dma-data.bin',0),
      ('worker-done','accepted/live/attempt-0/halt/irq-stack-after.bin',3072+34*4),
      ('admission-prior','accepted/live/attempt-1/preflight.json',0))
    caught=[]
    for name,rel,offset in cases:
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)/'artifact';shutil.copytree(root,dst)
            shutil.copytree(root.parent/'accele160-dma-suspend-20261017',
                            Path(td)/'accele160-dma-suspend-20261017')
            flip(dst/rel,offset)
            try:v.verify(dst)
            except (ValueError,AssertionError,KeyError,UnicodeDecodeError,json.JSONDecodeError):
                caught.append(name)
            else:raise AssertionError('tamper accepted: '+name)
    print(json.dumps(dict(replay=baseline,tamper_rejected=caught),indent=2))

if __name__=='__main__':main(Path(sys.argv[1]))
