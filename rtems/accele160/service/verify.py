#!/usr/bin/env python3
"""Replay saved card command replies, without hardware or executing capture data."""
import argparse,json,struct
from pathlib import Path

def verify(path):
    records=[json.loads(s) for s in Path(path).read_text().splitlines()]
    counts={'reply':0,'selftest':0,'selftest_pass':0,'idle_gate':0}
    for r in records:
        event=r['event']
        if event in counts:counts[event]+=1
        if event not in ('reply','selftest'):continue
        b=bytes.fromhex(r['wire']);assert len(b)==896
        w=struct.unpack_from('<32I',b)
        assert w[16]==r['seq'] and w[24]==0x31435653 and 0<w[19]<=768
        assert w[17]==r.get('expected',r.get('status'))
        text=b[128:128+w[19]].decode('ascii')
        if event=='reply':assert w[18]==r['epoch'] and text==r['text']
        if w[17]:assert text==f'error={w[17]}\n'
        else:
            op=r.get('opcode')
            if op==2:assert text=='RTEMS 4.6.6 / AcceleRAID160 / SVC1\n'
            if op==3:assert text==f'ticks={w[20]}\ntick_ms=10\n'
    assert counts['selftest_pass']>=1
    return counts
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('journal',type=Path);a=p.parse_args()
    print(json.dumps(verify(a.journal),indent=2))
