#!/usr/bin/env python3
"""Build bounded Tetris requests or split a verified BIO1 response."""
import argparse
from pathlib import Path
import struct
STATE_BYTES=240
RESPONSE_BYTES=2160

def request(state=None,seed=0,key=0,ticks=1):
    if state is None:
        if not 0<=seed<=0xffffffff:raise ValueError('seed outside uint32')
        return struct.pack('<4I',1,seed,0,0)+bytes(STATE_BYTES)
    if len(state)!=STATE_BYTES or key not in (0,ord('a'),ord('d'),ord('w'),ord('s'),ord('q')) or not 0<=ticks<=20:
        raise ValueError('invalid state length, key or tick count')
    return struct.pack('<4I',0,0,key,ticks)+state

def split(data):
    if len(data)!=RESPONSE_BYTES:raise ValueError('wrong Tetris response length')
    frame=data[STATE_BYTES:]
    if any(c<32 or c>126 for c in frame):raise ValueError('nonprintable framebuffer')
    return data[:STATE_BYTES],''.join(frame[i:i+80].decode('ascii')+'\n' for i in range(0,1920,80))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state',type=Path);p.add_argument('--seed',type=lambda s:int(s,0),default=0)
    p.add_argument('--key',choices=['a','d','w','s','q']);p.add_argument('--ticks',type=int,default=1)
    p.add_argument('--response',type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    if a.response:
        state,frame=split(a.response.read_bytes())
        a.output.mkdir(exist_ok=False,parents=True)
        (a.output/'state.bin').write_bytes(state);(a.output/'frame.txt').write_text(frame)
    else:
        data=request(a.state.read_bytes() if a.state else None,a.seed,ord(a.key) if a.key else 0,a.ticks)
        with a.output.open('xb') as f:f.write(data)
if __name__=='__main__':main()
