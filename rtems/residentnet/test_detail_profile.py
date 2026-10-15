#!/usr/bin/env python3
"""Detail metadata refuses mismatched modes, CPU sums, padding and launch policy."""
import struct
from presentation_profile import decode,preflight,OFFSET
opt=dict(cpu_profile=True,frame_profile=True,detail_test=True,no_fnv=True,direct_frame=True,double_buffer=True)
for g in range(1,53):
 b=bytearray(65536);struct.pack_into('<16I',b,OFFSET,0x31524650,1,g,2,100,60,30,10,20,0,0,100,0,0,10,0)
 struct.pack_into('<12I',b,OFFSET+64,0x31555043,1,int(17<=g<=40),10,8,5,2,1,1,0,0,0)
 d=decode(b,g,False,opt);assert d['cpu_samples']['render']==8
 for offset,value in [(OFFSET+64+8,1-int(17<=g<=40)),(OFFSET+64+16,9),(OFFSET+64+20,100),(OFFSET+64+40,1),(65535,1)]:
  bad=bytearray(b)
  if offset==65535:bad[offset]=value
  else:struct.pack_into('<I',bad,offset,value)
  try:decode(bad,g,False,opt)
  except AssertionError:pass
  else:raise AssertionError((g,offset))
preflight(opt,True,True,False)
for pipeline,test,load in [(False,True,False),(True,False,False),(True,True,True)]:
 try:preflight(opt,pipeline,test,load)
 except AssertionError:pass
 else:raise AssertionError('unsafe detail test launch')
print('PASS 52 detail modes; CPU sample sums/bounds/reserved fields; bounded launch policy')

# Runtime mode accepts either renderer state, never arbitrary values. Fixed
# benchmark builds retain their stricter expected-mode assertion above.
runtime=dict(opt,detail_test=False,runtime_detail=True)
preflight(runtime,True,False,False)
for mode in (0,1):
 struct.pack_into('<I',b,OFFSET+72,mode)
 assert decode(b,52,False,runtime)['detail']==mode
for mode in (2,0xffffffff):
 struct.pack_into('<I',b,OFFSET+72,mode)
 try:decode(b,52,False,runtime)
 except AssertionError:pass
 else:raise AssertionError('invalid runtime detail accepted')
try:preflight(dict(opt,runtime_detail=True),True,True,False)
except AssertionError:pass
else:raise AssertionError('scripted detail mixed with runtime selection')
print('PASS runtime high/low states; malformed detail rejected; fixed-mode policy preserved')
