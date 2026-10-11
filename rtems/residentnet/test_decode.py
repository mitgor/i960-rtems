#!/usr/bin/env python3
"""Malformed/contradictory decode evidence cannot qualify the internal path."""
import copy
from decode_audit import decode
pages=[[0]*150+[0x32484343,i]+[0]*8 for i in range(1,8)]
pages[0][159]=0x26
pages[3][152:]=[0xa5a5a5a5,0x5a5a5a5a,0xa5a5,0x5a5a,0x26,0x26,0x7221,0]
pages[5][152:]=[0xc004fe20,0xc004c3b0,0xc004c3b0,0xc004fe50,0xc004fe80,0xc004c3b0,0xc004c3b0,0xc004feb0]
pages[6][152:]=[6,0xc000d540,0xc004fc40,0xc0050430,0x1000000,1,0xe0600000,0xe0600005]
assert decode(pages)['internal_cpu_path_qualified']
for page,index in [(3,i) for i in range(152,158)]+[(i,151) for i in range(7)]:
 bad=copy.deepcopy(pages);bad[page][index]^=1
 try:decode(bad)
 except AssertionError:pass
 else:raise AssertionError('invalid positive control accepted')
for page,index in [(5,i) for i in range(152,160)]+[(6,i) for i in (152,153,154,155,158,159)]:
 bad=copy.deepcopy(pages);bad[page][index]^=1
 result=decode(bad);assert not result['internal_cpu_path_qualified'] and not result['broader_ram_owned']
print('13 malformed controls rejected; 14 contradictory dispatch fields cannot qualify; RAM grant remains false')
