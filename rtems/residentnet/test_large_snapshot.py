#!/usr/bin/env python3
from large_contract import validate_large
w=[0]*64
mib=12;size=mib*1048576;lo=0xc0240000
w[:19]=[0x314d4152,lo,size,1,4,size,0,0,lo+64,262144,lo+0x40080,65536,4,lo+0x90000,size-0x90000-64,100,1,0xc0002050,0]
w[19:31]=[4,2048,65536,65536,65536,2,2,2,lo+4096,131072,0,0]
validate_large(w,mib,revision=2)
w[18]=w[14]//4;w[29:31]=[131072,1]
validate_large(w,mib,True,2)
for index in list(range(15))+[16,18,19,21,22,23,26,28,29,30,31,63]:
 bad=w.copy();bad[index]^=1
 try:validate_large(bad,mib,True,2)
 except AssertionError:pass
 else:raise AssertionError(index)
for index,value in [(17,lo),(24,0),(25,0),(27,lo),(27,lo+262144),(26,0)]:
 bad=w.copy();bad[index]=value
 try:validate_large(bad,mib,True,2)
 except AssertionError:pass
 else:raise AssertionError((index,value))
print('RAM1: layout, full final scan, stack stress, workspace proof and revision corruption rejected')

from large_contract import validate_large_stacks
s=[0]*64;s[2]=2
for n,i in enumerate((16,26)):
 s[i]=0xc0241000+n*4096;s[i+1]=0xc0280090+n*65664;s[i+2]=s[i+1]+65536;s[i+3]=s[i+1]+64;s[i+8]=100
validate_large_stacks(s)
for i in (17,18,19,27,28,29):
 bad=s.copy();bad[i]^=1
 try:validate_large_stacks(bad)
 except AssertionError:pass
 else:raise AssertionError(i)
print('External task stack ranges and actual interrupt frames checked')

validate_large(w,mib,False,2,transition=True)
for transition in (False,True):
 bad=w.copy();bad[18]-=1
 try:validate_large(bad,mib,False,2,transition=transition)
 except AssertionError:pass
 else:raise AssertionError('partial final scan accepted')
try:validate_large(w,mib,False,2)
except AssertionError:pass
else:raise AssertionError('unrequested transition accepted')
print('Authorized cross-page STOP transition accepted; partial and unrequested shutdown rejected')
