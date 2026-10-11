#!/usr/bin/env python3
"""Audit the linked owned-stack trampoline and allocation before a card test."""
import argparse,json,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('build',type=Path);a=p.parse_args()
symbols={}
for line in (a.build/'kernel.symbols').read_text().splitlines():
    fields=line.split()
    if len(fields)==3:symbols[fields[2]]=int(fields[0],16)
base=symbols['_irq_owned_area'];end=base+16512
assert base%16==0 and 0xc0f4c010<=base<end<=0xc0f9bff0
text=(a.build/'kernel.dis').read_text()
m=re.search(r'^\w+ <_timer_isr>:\n(.*?)(?=^\w+ <owned_reentry>:)',text,re.M|re.S)
assert m,'owned entry missing'
body=m[1]
for instruction in ['stq\tg0,','stq\tg4,','stq\tg8,','stq\tg12,',
                    'ldq\t(r5),g0','ldq\t0x10(r5),g4','ldq\t0x20(r5),g8','ldq\t0x30(r5),g12',
                    'mov\tr4,sp','modtc\tr7,r6,r7','<_irq_owned_enter>','<_irq_owned_leave>']:
    assert instruction in body,instruction
assert '<_irq_owned_area+0xc0>,sp' in body
assert body.index('stq\tg12,')<body.index('<_irq_owned_enter>')
assert body.index('<_irq_owned_leave>')<body.index('ldq\t(r5),g0')<body.index('mov\tr4,sp')
# Original frame is only read here. Never synthesize PC/AC/PFP or store via FP.
assert not re.search(r'\bst\w*\t[^\n]*\(fp\)',body)
assert '0xfe,r7' in body,'TC reserved/event bits must not be written'
print(json.dumps(dict(owned_area=hex(base),end=hex(end),hardware_frame='retained in place',
                      globals='four quadword saves/restores',trace_mask='0xfe',passed=True)))
