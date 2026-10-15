#!/usr/bin/env python3
import copy
from verify_drain import validate_drain
r=[[0x314e5244,2,4166700]+[0]*61 for _ in range(2)]
r[1][3:13]=[1000000,900000,250000,1000,10,11,6,0,1,1]
assert validate_drain(r,11000)['worker_tick_deltas']==[6,0]
for key,value in [(0,0),(1,1),(2,1),(5,0),(9,0),(11,2),(13,1)]:
 b=copy.deepcopy(r);b[-1][key]=value
 try:validate_drain(b,11000)
 except AssertionError:pass
 else:raise AssertionError(key)
try:validate_drain(r,59855)
except AssertionError:pass
else:raise AssertionError('gap accepted')
b=copy.deepcopy(r);b.append(copy.deepcopy(b[-1]));b[-1][5]+=1
try:validate_drain(b,11000)
except AssertionError:pass
else:raise AssertionError('completed timing mutated')
print('PASS drain schema, immutable completed reports, corruption and 20 ms IRQ acceptance gate')
