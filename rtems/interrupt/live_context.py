#!/usr/bin/env python3
"""Explicit bounded owned-stack/context stress on the patched card."""
import argparse,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board

def decode(data):
    assert len(data)==392,len(data)
    w=struct.unpack('<98I',data)
    assert w[0]==0x31515249 and w[1]==0,w[:2]
    assert w[16]==0x31584349
    assert w[2]==w[17] and w[17]>=8,w[17]
    assert w[18]==w[19]==w[28]==0,w[18:20]
    base=w[26];assert base+192<=w[20]<=w[21]<base+w[27]-64
    assert w[7]==0x10c7 and w[8]==0x80000 and w[9]==w[10]
    assert w[11]==w[12]==w[13]==w[15]==0 and not(w[14]&0x2000)
    assert w[29]==0xc0001000,'base interrupt-stack pointer changed'
    assert w[30:45]==tuple(0x19600000+i for i in range(15)), 'missing global sentinels'
    assert w[30:46]==w[46:62], 'global register corruption'
    assert w[66:78]==tuple(0x96000000+i for i in range(4,16)), 'missing local sentinels'
    assert w[65]==1000000 and w[81]==0, 'bounded counter did not finish'
    for i in range(16):
        if i not in (2,3):assert w[62+i]==w[78+i],('local',i)
    assert w[94]==w[95] and w[96]==w[97], 'PC/TC changed'
    return dict(interrupts=w[17],faults=w[18],probe_failures=w[19],owned_area=hex(base),
                sampled_stack_low=hex(w[20]),sampled_stack_high=hex(w[21]),
                sampled_usage_bytes=w[21]-(base+192),hardware_frame=hex(w[22]),
                saved_pc=hex(w[23]),saved_ac=hex(w[24]),vector=hex(w[25]),
                pc_before=hex(w[94]),pc_after=hex(w[95]),tc_before=hex(w[96]),tc_after=hex(w[97]))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['payload','module','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--runs',type=int,default=3);a=p.parse_args()
    board=Board(a.payload,a.module,a.output);rows=[]
    try:
        for i in range(a.runs):
            data=board.step(b'');(a.output/f'context-{i}.bin').write_bytes(data)
            row=decode(data);rows.append(row);print(json.dumps(row),flush=True)
        (a.output/'acceptance.json').write_text(json.dumps(rows,indent=2)+'\n')
    finally:print(json.dumps(board.close()),flush=True)
if __name__=='__main__':main()
