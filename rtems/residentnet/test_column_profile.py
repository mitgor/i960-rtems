#!/usr/bin/env python3
"""Reject wrong implementation/case count and unbounded column experiments."""
import struct
from presentation_profile import decode,preflight,OFFSET
opt=dict(cpu_profile=True,frame_profile=True,column_test=True,low_detail=True,no_fnv=True,direct_frame=True,double_buffer=True)
for g in range(1,53):
 b=bytearray(65536);struct.pack_into('<16I',b,OFFSET,0x31524650,1,g,2,100,60,30,10,20,0,0,100,0,0,10,0)
 mode=1 if 17<=g<=28 else 2 if 29<=g<=40 else 0
 struct.pack_into('<12I',b,OFFSET+64,0x31555043,1,1,10,8,5,2,1,1,0,mode,96)
 assert decode(b,g,False,opt)['column_mode']==mode
 for offset,value in [(OFFSET+64+40,(mode+1)%3),(OFFSET+64+44,95),(65532,1)]:
  bad=bytearray(b);struct.pack_into('<I',bad,offset,value)
  try:decode(bad,g,False,opt)
  except AssertionError:pass
  else:raise AssertionError((g,offset))
preflight(opt,True,True,False)
for pipeline,test,load in [(False,True,False),(True,False,False),(True,True,True)]:
 try:preflight(opt,pipeline,test,load)
 except AssertionError:pass
 else:raise AssertionError('unsafe column test launch')
print('PASS 52 implementation IDs and self-test counts; bounded admission')
