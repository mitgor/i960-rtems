#!/usr/bin/env python3
"""Reject altered flash, suspend ordering, channel, payload and ownership evidence."""
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
      ('inventory-channel0','accepted/live/fresh-inventory/halt/irq-stack-after.bin',3072+44*4),
      ('owner','accepted/live/attempt-0/owner-after.bin',0x2a0),
      ('dma-active-stop','accepted/live/attempt-0/halt/irq-stack-after.bin',3072+82*4),
      ('suspend-tick','accepted/live/attempt-1/halt/irq-stack-after.bin',3072+84*4),
      ('hold-stability','accepted/live/attempt-1/halt/irq-stack-after.bin',3072+91*4),
      ('resume-ccr','accepted/live/attempt-1/halt/irq-stack-after.bin',3072+87*4),
      ('final-descriptor','accepted/live/attempt-1/halt/irq-stack-after.bin',3072+45*4),
      ('host-payload','accepted/live/attempt-0/halt/dma-data.bin',0),
      ('worker-done','accepted/live/attempt-0/halt/irq-stack-after.bin',3072+34*4),
      ('prior-channel','accepted/live/attempt-1/preflight.json',0))
    caught=[]
    for name,rel,offset in cases:
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)/'artifact';shutil.copytree(root,dst)
            flip(dst/rel,offset)
            try:v.verify(dst)
            except (ValueError,AssertionError,KeyError,UnicodeDecodeError,json.JSONDecodeError):
                caught.append(name)
            else:raise AssertionError('tamper accepted: '+name)
    print(json.dumps(dict(replay=baseline,tamper_rejected=caught),indent=2))

if __name__=='__main__':main(Path(sys.argv[1]))
