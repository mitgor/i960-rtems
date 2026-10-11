#!/usr/bin/env python3
"""Reject malformed shared-heap evidence; counter carry remains valid."""
from copy import deepcopy
from verify_heap_diagnostics import validate_diagnostics

def record(ticks,retired):
 w=[0]*64;w[:5]=[0x314c5348,2,4166700,0xffffffff,1]
 elapsed=(ticks-1)*41667
 w[5:12]=[ticks,42000,500,elapsed&0xffffffff,elapsed>>32,41000,41667]
 for op in range(8):w[12+op*4:16+op*4]=[100,50,4000,0]
 w[44:49]=[retired,retired,100,100,100]
 w[52:64]=[retired-1,100,0,1,retired,10,10,3,200,200,0,1]
 return w
records=[record(100000,20),record(180000,30)]
final=[0]*64;final[5]=180000;final[50]=200
result=validate_diagnostics(records,final)
assert result['irq_samples']==180000 and records[-1][9]>0
cases=[(0,0),(1,4),(2,1),(3,0),(4,0),(5,1),(6,0),(7,41668),
 (10,43000),(11,0),(12,0),(13,0),(14,1),(14,5001),
 (44,29),(45,31),(49,1),(50,1),(51,1),(54,11),(55,0),
 (57,9),(58,9),(59,0),(60,201),(61,201),(62,1),(63,0)]
for index,value in cases:
 bad=deepcopy(records);bad[-1][index]=value
 try:validate_diagnostics(bad,final)
 except AssertionError:pass
 else:raise AssertionError(('accepted corrupted diagnostic',index,value))
# Legacy schema is retained for the pre-optimization physical baseline.
legacy=deepcopy(records)
for w in legacy:w[1]=1;w[57:59]=[0xffffffff,123]
assert validate_diagnostics(legacy,final)['unlocked_copy_preemptions'] is None
print(f'Shared diagnostics: 64-bit carry, both schemas, {len(cases)} corruptions rejected')

latest=deepcopy(records)
for w in latest:w[1]=3;w[56]=7
assert validate_diagnostics(latest,final)['large_workload_allocation_refusals']==7
print('Version 3: nonfatal large-allocation refusal telemetry checked')
