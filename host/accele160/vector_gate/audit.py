#!/usr/bin/env python3
"""Construct one pinned AcceleRAID vector/timer observation candidate."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'helper'))
from audit_late_ping import CAVE, LOADER_BASE, LOADER_RETURN
from audit_dispatch_rehearsal import analyze

STOCK_SHA = '0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a'
CURRENT_SHA = 'ef5635d38bf397ff13fa1140ef6265de0b300c70ad8b157c17427013a1d2abb5'
OLD_HANDLER_SHA = '0a9c5f9deaae6f01d943c90a065a31de377ebbcf388a28b3e73b0ba96b6192e8'
HANDLER_SHA = 'dd4d51c24ef1debcbc1dc4830c0761696be94849082965146445f38e2662c52f'
PREFIX_SHA = '6d6e22c11a26ce404f3ef4ac90c382d40e521aeca745903cd7346eea5a804148'
CANDIDATE_SHA = '93faf91f553822665cd4125d90b1066370c4bca0da76af8336daf98bc2dae094'

def sha(d): return hashlib.sha256(d).hexdigest()

def make(stock, current, old_handler, handler, prefix):
    if len(stock)!=1048576 or len(current)!=len(stock): raise ValueError('flash length')
    for label,data,digest in [('stock',stock,STOCK_SHA),('current',current,CURRENT_SHA),('old handler',old_handler,OLD_HANDLER_SHA),('handler',handler,HANDLER_SHA),('prefix',prefix,PREFIX_SHA)]:
        if sha(data)!=digest: raise ValueError(label+' identity')
    if len(old_handler)!=3392 or len(handler)!=3868 or len(prefix)!=80 or handler.count(prefix)!=1:
        raise ValueError('handler or exact prefix size')
    baseline=analyze(stock); now=analyze(current)
    if now['runtime']!=baseline['runtime'] or current[0xf0000:]!=stock[0xf0000:]:
        raise ValueError('runtime/boot drift')
    base,size,trailer=(baseline['loader']['flash_offset'],baseline['loader']['size'],baseline['trailer_offset'])
    cave=base+CAVE-LOADER_BASE; hook=base+LOADER_RETURN-LOADER_BASE
    if current[cave:cave+len(old_handler)]!=old_handler or current[cave+len(old_handler):cave+len(handler)]!=b'\xff'*(len(handler)-len(old_handler)):
        raise ValueError('handler preimage')
    image=bytearray(current);image[cave:cave+len(handler)]=handler
    loader_sum=sum(struct.unpack_from(f'<{size//4}I',image,base))&0xffffffff
    struct.pack_into('<I',image,trailer+24,loader_sum)
    trailer_sum=sum(struct.unpack_from('<31I',image,trailer))&0xffffffff
    struct.pack_into('<I',image,trailer+124,trailer_sum)
    checked=analyze(image)
    changed={i for i,(a,b) in enumerate(zip(current,image)) if a!=b}
    allowed=set(range(cave,cave+len(handler)))|set(range(trailer+24,trailer+28))|set(range(trailer+124,trailer+128))
    if not changed<=allowed or checked['runtime']!=baseline['runtime'] or not checked['loader']['checksum_passed'] or not checked['trailer_checksum_passed'] or image[0xf0000:]!=stock[0xf0000:] or image[hook:hook+4]!=current[hook:hook+4]:
        raise ValueError('candidate changed non-cave firmware or invalid checksum')
    if CANDIDATE_SHA and sha(image)!=CANDIDATE_SHA: raise ValueError('candidate identity')
    return bytes(image),dict(candidate_sha256=sha(image),current_sha256=CURRENT_SHA,handler_sha256=HANDLER_SHA,changed_bytes=len(changed),loader_checksum=f'0x{loader_sum:08x}',trailer_checksum=f'0x{trailer_sum:08x}',runtime_unchanged=True,boot_block_unchanged=True,flash_written=False)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('stock','current','old_handler','handler','prefix','output'):p.add_argument(name,type=Path)
    a=p.parse_args()
    image,receipt=make(*(getattr(a,n).read_bytes() for n in ('stock','current','old_handler','handler','prefix')))
    if a.output.exists():raise FileExistsError(a.output)
    a.output.write_bytes(image)
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
