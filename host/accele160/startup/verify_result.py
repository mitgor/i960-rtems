#!/usr/bin/env python3
"""Offline acceptance of a future guarded 16-byte probe result; no transport."""
import argparse
import struct
from pathlib import Path

def verify(data,nonce):
    if not 0<=nonce<=0xffffffff:raise ValueError('nonce outside uint32')
    if len(data)!=144:raise ValueError('expected 64-byte guards around 16-byte result')
    if data[:64]!=b'\xa5'*64 or data[80:]!=b'\xa5'*64:raise ValueError('guard change')
    expected=(0x444f4e45,nonce,496,nonce^0x96016001)
    if struct.unpack_from('<4I',data,64)!=expected:raise ValueError('incomplete/stale/wrong result')
    return True

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--nonce',type=lambda x:int(x,0),required=True)
    a=p.parse_args();verify(a.capture.read_bytes(),a.nonce);print('record/guards match; caller return and DMA quiescence require separate evidence')
