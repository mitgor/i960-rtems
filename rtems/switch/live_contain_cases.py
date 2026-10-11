#!/usr/bin/env python3
import argparse,json,struct
from pathlib import Path
from live_contain import decode as base_decode

def decode(data):
 assert len(data)==1024
 w=list(struct.unpack('<256I',data));c=w[236:];d=w[184:204];q=w[204:236];mode=c[0]
 assert mode in (1,2)
 assert c[1:4]==[16,28,40] and 40<=c[4]<=44 and c[5:11]==[2,1,1,0,8,8]
 assert c[11:]==[40,0,12,12,0,24,mode,0,0]
 assert d[2]==(17 if mode==1 else 29) and d[2]<d[3]<(28 if mode==1 else 40)
 assert d[7]==(3 if mode==1 else 2) and q[2:4]==[40,44]
 # Reuse unchanged quarantine invariants after validating the differing fields.
 w[186]=8;w[187]=40;w[191]=1
 row=base_decode(struct.pack('<236I',*w[:236]));row['stop_tick']=d[3]
 row['critical']=dict(mode=mode,ready_tick=d[2],controller_tick=c[11],outer_return_tick=c[4],depth=d[7]-1,observations=c[13:15],pending=c[16])
 return row

if __name__=='__main__':
 from live_contain import main
 main(decode,(1,2,1,2,1,2),'containcases.bin')
