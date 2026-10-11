#!/usr/bin/env python3
"""Explicit bounded two-task interrupt-continuation acceptance on hardware."""
import argparse,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board

def decode(data):
    assert len(data)==736,len(data)
    w=struct.unpack('<184I',data)
    assert w[0]==0x31575349 and w[1]==0,('header',w[:20])
    assert w[2]>=32 and w[3]>5 and w[4]>5,w[2:5]
    assert w[5:7]==(1,1) and w[7:11]==(0,0,0,0),w[5:11]
    assert w[11]==0x10c7 and w[12]==0x80000 and w[13]==w[14]
    assert w[15:18]==(0,0,0) and not(w[18]&0x2000) and w[19]==0
    slots=[]
    for i in range(2):
        offset=20+i*82;s=w[offset:offset+12];r=w[offset+12:offset+82]
        assert s[0] and s[1]+16<=s[3]<=s[2]-64 and s[6]==0xf2
        assert s[7]==0 and s[8]==s[9] and s[8]>5,s
        assert s[10]+192<=s[11]<s[10]+8128,s
        assert r[:15]==tuple(0x19600000+i*0x10000000+j for j in range(15))
        assert r[:16]==r[16:32],('globals',i)
        for j in range(16):
            if j not in (2,3,5):assert r[32+j]==r[48+j],('locals',i,j)
        assert r[38:48]==tuple(0x96000000+j for j in range(6,16))
        assert r[64]==r[65] and r[66]==r[67] and r[68]==0
        assert 0<r[69]<=1000000 and r[53]!=0,('stop/budget',i)
        slots.append(dict(owner=hex(s[0]),task_stack=[hex(s[1]),hex(s[2])],frame=hex(s[3]),
                          entries=s[8],returns=s[9],irq_stack=hex(s[10]),sampled_sp=hex(s[11]),
                          remaining_budget=r[69],pc=hex(r[64]),tc=hex(r[66])))
    assert slots[0]['owner']!=slots[1]['owner'] and slots[0]['irq_stack']!=slots[1]['irq_stack']
    a,b=[w[20+i*82:30+i*82] for i in range(2)]
    assert a[2]<=b[1] or b[2]<=a[1], 'task stacks overlap'
    return dict(ticks=w[2],two_live_observations=w[3],scheduler_handoffs=w[4],faults=w[1],slots=slots)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['payload','module','output']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--runs',type=int,default=3);a=p.parse_args();a.output.mkdir(exist_ok=False,parents=True)
    rows=[]
    for i in range(a.runs):
        board=Board(a.payload,a.module,a.output/f'run-{i}')
        try:
            data=board.step(b'');(board.out/'switch.bin').write_bytes(data)
            row=decode(data);rows.append(row);print(json.dumps(row),flush=True)
            (board.out/'acceptance.json').write_text(json.dumps(row,indent=2)+'\n')
        finally:print(json.dumps(board.close()),flush=True)
    (a.output/'acceptance.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()
