"""Exclusive synchronous BIO1 session client; close restores RAM in the kernel.

Linux/root only. Load dac960session with BIO1 firmware first. An error is never
retried. Retained/pinned state requires inspecting captures and rebooting.
"""
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'loadrun'))
import buffer_io as bio

class Session:
    def __init__(self):
        self.fd=os.open('/dev/i960-session',os.O_RDWR|os.O_CLOEXEC)
    def step(self,block):
        if len(block)!=bio.SIZE: raise ValueError('expected one BIO1 block')
        if os.write(self.fd,block)!=len(block): raise OSError('short session write')
        response=os.read(self.fd,bio.SIZE)
        if len(response)!=bio.SIZE: raise OSError('short session read')
        # Reuse independent whole-image verifier, with zeros outside the block.
        before=bytes(bio.OFFSET)+block+bytes(524288-bio.IMAGE_SIZE)
        after=bytes(bio.OFFSET)+response+bytes(524288-bio.IMAGE_SIZE)
        status,output=bio.response(before,after)
        return status,output,response
    def close(self,verify=True):
        if self.fd is not None:
            fd,self.fd=self.fd,None
            os.close(fd)
            # Linux ignores ->release's return value. Inspect the synchronous
            # final-release record instead of treating close(2) as an ACK.
            if verify:
                log=Path('/sys/kernel/debug/dac960session/result.txt').read_text()
                if 'SESSION CLOSE rc=0 pending=0 exec-dirty=0 stage-dirty=0' not in log:
                    raise RuntimeError('session close did not verify restoration; inspect debugfs; do not unload')
    def __enter__(self): return self
    def __exit__(self,*args): self.close()
