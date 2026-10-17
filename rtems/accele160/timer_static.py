#!/usr/bin/env python3
"""Count aligned direct references to candidate timer/interrupt registers in stock ROM.

This is a literal scan, not an ownership proof: base-relative or computed
addresses and run-time peripheral activity will not appear here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

HELPER=Path(__file__).resolve().parents[2]/'host/accele160/helper'
STARTUP=Path(__file__).resolve().parents[2]/'host/accele160/startup'
sys.path.insert(0,str(STARTUP))
from analyze import analyze
sys.path.insert(0,str(HELPER))
from verify_full_dump import unpack

STOCK_SHA='0a951782a7ccd1855746ffeb3a1b64563287bc56e0dce77d63b79c71ec3b502a'
REGISTERS={
 'timer1_reload_candidate':0xff000310,
 'timer1_count_candidate':0xff000314,
 'timer1_mode_candidate':0xff000318,
 'interrupt_pending_candidate':0xff008500,
 'interrupt_mask_candidate':0xff008504,
 'interrupt_config_candidate':0xff008510,
 'interrupt_map2_candidate':0xff008528,
}

def scan(blob,base):
    return {name:[f'0x{base+i:08x}' for i in range(0,len(blob)-3,4)
                  if blob[i:i+4]==struct.pack('<I',addr)]
            for name,addr in REGISTERS.items()}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stock',type=Path);a=p.parse_args()
    flash=a.stock.read_bytes()
    if hashlib.sha256(flash).hexdigest()!=STOCK_SHA:raise ValueError('not exact paired stock flash')
    info=analyze(flash)
    if not info['accepted_stock']:raise ValueError('stock image audit')
    loader=info['loader'];lo=flash[loader['flash_offset']:loader['flash_offset']+loader['size']]
    region=next(row for row in info['regions'] if row['selector']==2)
    start=info['runtime']['flash_zip_offset'];end=region['offset']+region['size']-0xa0
    runtime,_=unpack(flash[start:end])
    result=dict(stock_sha256=STOCK_SHA,runtime_sha256=hashlib.sha256(runtime).hexdigest(),
                loader=scan(lo,loader['destination']),runtime=scan(runtime,0xc0010000),
                scope='aligned direct 32-bit literal references only; no live register read or owner proof')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
