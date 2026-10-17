#!/usr/bin/env python3
"""Replay both accepted batches and reject seven independent capture edits."""
import importlib.util,json,shutil,sys,tempfile
from pathlib import Path

spec=importlib.util.spec_from_file_location(
    'handoff_verify',Path(__file__).with_name('verify_live.py'))
verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)

def flip(path,offset):
    b=bytearray(path.read_bytes());b[offset]^=1;path.write_bytes(b)

def main(root):
    baseline=verify.verify(root);caught=[]
    cases=(('flash-byte','live/post-flash-1/data.bin',0),
           ('owner-record','live/accept-0/owner-after.bin',0x2a0),
           ('irq-fault','live/accept-0/halt/irq-stack-after.bin',3072+9*4),
           ('stale-token','live/accept-0/halt/stale-page.bin',0xa4c),
           ('RTEMS-callback','live/accept-0/halt/irq-stack-after.bin',3072+17*4),
           ('task-progress','live/accept-0/halt/irq-stack-after.bin',3072+20*4),
           ('task-ISR-guard','live/accept-0/halt/task-irq-stack-after.bin',0))
    for name,rel,offset in cases:
        with tempfile.TemporaryDirectory() as td:
            dst=Path(td)/'artifact';shutil.copytree(root,dst)
            flip(dst/rel,offset)
            try:verify.verify(dst)
            except (ValueError,AssertionError):caught.append(name)
            else:raise AssertionError('tamper accepted: '+name)
    print(json.dumps(dict(replay=baseline,tamper_rejected=caught),indent=2))

if __name__=='__main__':main(Path(sys.argv[1]))
