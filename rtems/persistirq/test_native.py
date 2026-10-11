#!/usr/bin/env python3
import itertools,os,struct,subprocess,tempfile
from pathlib import Path
from build_transport import build
HERE=Path(__file__).resolve().parent

def closure(owners,waits,seed):
 seen={seed};front=[seed]
 while front:
  owner=front.pop()
  for task,r in enumerate(waits):
   if r and owners[r-1]==owner and task not in seen:seen.add(task);front.append(task)
 return sum(1<<i for i in seen)

def compile_gate(d):
 src=d/'gate.c';exe=d/'gate';src.write_text('#include <stdio.h>\n#include "report.h"\nint main(void){unsigned int w[320];while(fread(w,sizeof(w),1,stdin)==1)putchar(pirq_valid(w,w[4],w[3])?\'1\':\'0\');return 0;}\n')
 subprocess.run([os.environ.get('CC','cc'),'-Wall','-Wextra','-fsanitize=address,undefined','-I'+str(HERE),str(src),'-o',str(exe)],check=True);return exe

def fixture(q=False):
 w=[0]*320;w[:17]=[0x31515250,1,0,2 if q else 1,1,1,2 if q else 1,0,50,0,17,18,40,0 if q else 44,0 if q else 44,44 if q else 0,50]
 w[18]=int(q);w[23:27]=[0x10c7,0x80000,0xc0100000,0xc0100000];w[31]=1
 w[32:43]=[1,4 if q else 3,0x10203040 if q else 0x22000001,0xdead0001 if q else 0x22000001,int(q),1,1,0 if q else 1,2 if q else 3,0 if q else 1,0]
 w[43:50]=[0x11223344 if q else 0x44000001,0 if q else 0x10203040,0 if q else 0x33000001,0 if q else 1,0 if q else 1,0 if q else 3,7]
 w[50:60]=[0,1,0,1,2,0,2,0x402,0x402,2] if q else [4,4,0,0,0,0,2,2,2,2]
 w[60:64]=[10,11,12,13];w[64:68]=[1,1,0,0] if q else [0]*4;w[68:72]=[1]*4;w[72:76]=[0xc0200000+i*0x10000 for i in range(4)]
 w[76:80]=[10,11,1,1] if q else [0]*4
 if q:w[80:88]=[101,102,103,104]*2
 w[90]=1000;w[91]=6
 for i in range(2):
  n=96+i*82;live=int(q and i==0);low=w[72+(3 if i else 0)];irq=0xc0300000+i*0x10000
  w[n:n+12]=[0xc0101000+i*0x1000,low,low+8192,low+1024,0,0,0xf2,live,20,20-live,irq,irq+1024]
  r=n+12;w[r:r+15]=[0x19600000+i*0x10000000+j for j in range(15)]
  if not live:w[r+16:r+32]=w[r:r+16]
  w[r+69]=90000
 w[260:280]=[1,16,28,40,41,2,1,1,0,8,8,40,0,12,12,0,24,1,0,0]
 w[280:287]=[23,23,4,5,1,1,0 if q else 1];w[288:299]=[0xc0400000,0xc0401000,0xc0402000,0xc0402000,15,0 if q else 1,1,0,1,30,20];w[316:]=[1,1,0x514f4b31,1]
 return w

def pack(w):return struct.pack('<320I',*w)

def main():
 with tempfile.TemporaryDirectory() as tmp:
  d=Path(tmp);exe=d/'graph';subprocess.run([os.environ.get('CC','cc'),'-Wall','-Wextra','-fsanitize=address,undefined',str(HERE/'test_graph.c'),'-o',str(exe)],check=True)
  incoming=bytearray();expected=bytearray();count=0
  for owners in itertools.product(range(5),repeat=2):
   for waits in itertools.product(range(3),repeat=4):
    for closed in (0,7):
     for task,r in itertools.product(range(4),range(2)):
      mask=closure(owners,waits,task);rc=3 if waits[task] or owners[r]==task else 5 if closed&(1<<task) else 4 if owners[r]<4 and mask&(1<<owners[r]) else 0
      after=list(waits)
      if rc==0:after[task]=r+1
      incoming+=struct.pack('<9I',*owners,*waits,closed,task,r);expected+=struct.pack('<9I',mask,rc,*owners,*after,closed);count+=1
  assert subprocess.check_output([str(exe)],input=incoming)==expected
  gate=compile_gate(d);rows=[fixture(False),fixture(True)];assert subprocess.check_output([str(gate)],input=b''.join(map(pack,rows)))==b'11'
  bad=[]
  for w in rows:
   for index in (17,18,19,20,21,22,23,24,25,27,28,29,32,33,39,49,50,51,56,57,58,59,64,65,68,71,76,77,78,79,91,103,104,185,186,280,281,282,283,288,289,290,292,293,294,318,319):
    x=w.copy();x[index]=0 if x[index] else 1;bad.append(pack(x))
  assert subprocess.check_output([str(gate)],input=b''.join(bad))==b'0'*len(bad)
  q=fixture(True);q[3]=5;q[7]=1;q[6]=3;assert subprocess.check_output([str(gate)],input=pack(q))==b'0';q[36]=0;assert subprocess.check_output([str(gate)],input=pack(q))==b'1'
  payload=d/'payload';payload.write_bytes(bytes(4));build(d/'module',payload);s=(d/'module/stage_rehearsal.h').read_text();assert s.index('if(d->resident_open)')<s.index('if(d->pending || d->runner_uncertain)')
 print(f'Persistent IRQ: {count} graph admission/closure cases match independent reachability oracle; {len(bad)} unsafe report mutations rejected; terminal reference gate and ASan/UBSan passed.')
if __name__=='__main__':main()
