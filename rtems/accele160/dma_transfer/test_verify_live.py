#!/usr/bin/env python3
"""Reject altered flash, owner, DMA completion, host payload and prior state."""
import importlib.util,json,shutil,sys,tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('dma_verify',Path(__file__).with_name('verify_live.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

def flip(path,offset):
    b=bytearray(path.read_bytes());b[offset]^=1;path.write_bytes(b)

def main(root):
    baseline=v.verify(root);cases=(
      ('flash','accepted/live/post-reuse-expiry-flash-1/data.bin',0),
      ('owner','accepted/live/accept-reuse-halt/owner-after.bin',0x2a0),
      ('host-payload','accepted/live/accept-reuse-halt/halt/dma-data.bin',0),
      ('dma-state','accepted/live/accept-reuse-halt/halt/irq-stack-after.bin',3072+68*4),
      ('dma-dar','accepted/live/accept-reuse-halt/halt/irq-stack-after.bin',3072+73*4),
      ('dma-channel1','accepted/live/accept-reuse-expiry/expiry/irq-stack-after.bin',3072+53*4),
      ('dma-payload-guard','accepted/live/accept-reuse-expiry/expiry/dma-pin-after.txt',0),
      ('prior-channel','accepted/live/accept-reuse-expiry/preflight.json',0),
      ('stale-token','accepted/live/accept-reuse-halt/halt/stale-page.bin',0xa4c),
      ('worker-done','accepted/live/accept-reuse-expiry/expiry/irq-stack-after.bin',3072+34*4))
    caught=[]
    for name,rel,offset in cases:
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)/'artifact';shutil.copytree(root,dst)
            flip(dst/rel,offset)
            try:v.verify(dst)
            except (ValueError,AssertionError,KeyError,UnicodeDecodeError):caught.append(name)
            else:raise AssertionError('tamper accepted: '+name)
    print(json.dumps({'replay':baseline,'tamper_rejected':caught},indent=2))
if __name__=='__main__':main(Path(sys.argv[1]))
