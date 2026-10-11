#!/usr/bin/env python3
"""Replay gate rejects inconsistent heap ownership and undrained allocation state."""
from verify import snapshot_gate
w=[0]*64
w[0]=0x31525845;w[1]=1;w[2]=2;w[3]=2;w[8:10]=[1,1]
w[12:16]=[100]*4;w[42:46]=[2,0,578,81916]
w[48:52]=[0xc022ee80,69952,200,200];w[56]=7;w[57]=0x36544e52;w[63]=31
snapshot_gate(w,7,True,True,True,True)
for index,value in ((48,0xc0200040),(49,69953),(50,201),(51,199),(57,0x35544e52),(59,129),(63,15)):
 bad=w.copy();bad[index]=value
 try:snapshot_gate(bad,7,True,True,True,True)
 except AssertionError:pass
 else:raise AssertionError((index,value))
w[2]=1;w[3]=0;w[8:10]=[0,0];w[53]=0x2000;w[50]=202
snapshot_gate(w,7,True,True,True,True)
w[50]=203
try:snapshot_gate(w,7,True,True,True,True)
except AssertionError:pass
else:raise AssertionError('more than two retained worker allocations accepted')
print('RNT6: active/parked ownership, heap bounds, retained count and final drain checked')

w[57]=0x37544e52;w[50]=205
snapshot_gate(w,7,True,True,True,True)
w[3]=1
snapshot_gate(w,7,True,True,True,True,stopping=True)
try:snapshot_gate(w,7,True,True,True,True)
except AssertionError:pass
else:raise AssertionError('unacknowledged STOP transition accepted')
w[3]=2
try:snapshot_gate(w,7,True,True,True,True,stopping=True)
except AssertionError:pass
else:raise AssertionError('unexpected active deadline reason accepted')
print('RNT7: temporary copy allocations and acknowledged STOP transition checked')

from verify import deadline_gate
w[5]=180001;w[8:10]=[1,0]
snapshot_gate(w,7,True,True,True,True,deadline=180000)
deadline_gate(w,180000)
for tick in (179999,180101):
 bad=w.copy();bad[5]=tick
 try:snapshot_gate(bad,7,True,True,True,True,deadline=180000)
 except AssertionError:pass
 else:raise AssertionError('out-of-window deadline transition accepted')
 try:deadline_gate(bad,180000)
 except AssertionError:pass
 else:raise AssertionError('out-of-window final deadline accepted')
print('RNT7: deadline-authorized drain transition and 100-tick acceptance bound checked')
