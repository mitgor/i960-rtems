#!/usr/bin/env python3
"""Independent arithmetic oracle for bounded benchmark frame trailers."""
import argparse,json,struct,statistics
from pathlib import Path
N=1048576
NAMES=['integer xorshift','1 KiB read','4 KiB read','64 KiB read','320-byte stride','64 KiB word copy','64 KiB word clear','1 KiB read with 4096 invalidations']
def expected(k):
 if k==0:
  h=1
  for _ in range(N):
   h^=(h<<13)&0xffffffff;h^=h>>17;h^=(h<<5)&0xffffffff
  return h
 if k==5:return 123
 if k==6:return 63
 mask={1:255,2:1023,3:16383,4:16383,7:255}[k]
 stride=80 if k==4 else 1
 return (1+sum((i*stride)&mask for i in range(N)))&0xffffffff
EXPECTED=[expected(k) for k in range(8)]
def decode(status,address,regs):
 default,a0,m0,a1,m1=regs
 matches=[a for a,m in ((a0,m0),(a1,m1)) if m&1 and ((address^a)&(m&0xfffff000))==0]
 assert len(matches)<=1,'overlapping logical templates'
 attributes=matches[0] if matches else default
 return dict(global_enabled=bool(status&1),data_cache_bytes=(((status>>16)&4095)+1)*(1<<((status>>12)&15))*(1<<((status>>8)&15))*(1<<((status>>4)&15)),template_matches=len(matches),region_cache_enabled=bool(attributes&2),effective_cache_enabled=bool(status&1 and attributes&2))
def verify(data):
 assert len(data)==65536,'whole frame required'
 r=struct.unpack_from('<128I',data,65024)
 assert r[0:2]==(0x31424343,2) and 1<=r[2]<=120
 assert r[3]==((r[2]-1)&7) and r[4]==N
 assert r[5]>0,'timer resolution insufficient'
 assert r[6]==EXPECTED[r[3]],'workload result'
 assert r[7]==r[8],'cache state changed'
 assert r[9]%4==0 and r[10:12]==(16384,1) and not any(r[17:])
 return dict(generation=r[2],case=r[3],ms=r[5],result=r[6],dcache_status=r[7],address=hex(r[9]),logical_registers=[hex(v) for v in r[12:17]],cache=decode(r[7],r[9],r[12:17]))
def main():
 p=argparse.ArgumentParser();p.add_argument('frames',type=Path,nargs='+');a=p.parse_args()
 rows=[verify(f.read_bytes()) for f in a.frames]
 groups=[]
 for k in range(8):
  v=[r['ms'] for r in rows if r['case']==k]
  if v:groups.append(dict(case=k,name=NAMES[k],samples=v,median_ms=statistics.median(v)))
 print(json.dumps(dict(rows=rows,groups=groups),indent=2))
if __name__=='__main__':main()
