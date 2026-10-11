#!/usr/bin/env python3
import os,struct,subprocess,tempfile
from pathlib import Path
from build_transport import build
HERE=Path(__file__).resolve().parent

def fixture(mode):
 w=[0]*256;w[:17]=[0x3149524f,1,0,mode,7,48,10,20,30,40,40,43,44,0,90000,80000,10000]
 w[18:22]=[0x10c7,0x80000,0xc0123000,0xc0123000];w[32:51]=[2,2,2,1,1,0x10203040,1,2,7,3,0x55667788,0x55667788,0,1,1,1,3,1,0]
 w[51:55]=[1,1,1,23];w[60:80]=[mode,16,28,40,41,2,1,1,0,8,8,40,0,12,12,0,24,2 if mode==2 else 1,0,0]
 w[8]=30 if mode==2 else 18
 w[244:]=[10,11,12,0xc1000000,0xc1000000,0,1,1,0,999,0x4d554f4b,0x514f4b31]
 if mode>=3:
  w[8]=w[9]=w[10]=18;w[11]=w[13]=22;w[12]=0;w[28:32]=[10,1,1,0];w[33]=0x402
  w[36:40]=[0,0,0,0];w[41:45]=[4,0x10203040,0xdeadbeef,0];w[47:50]=[0,5,0];w[55:60]=[70000,123,123,456,456];w[78:80]=[789,789];w[249:252]=[1,1,0]
  if mode==4:w[8]=18;w[9]=w[10]=40;w[11]=w[13]=44
  if mode==5:w[11]=w[52]=0;w[44]=1;w[48]=4
 for i in range(2):
  n=80+i*82;live=int(i==1 or mode>=3);low=0xc0200000+i*0x10000;irq=0xc0300000+i*0x10000
  w[n:n+12]=[0xc0100000+i*0x10000,low,low+8192,low+1024,0,0,0xf2,live,20,20-live,irq,irq+1024]
  r=n+12;w[r:r+15]=[0x19600000+i*0x10000000+j for j in range(15)]
  if not live:w[r+16:r+32]=w[r:r+16]
  w[r+69]=80000 if i else (70000 if mode>=3 else 90000)
 return w

def compile_gate(d):
 source=d/'gate.c';exe=d/'gate';source.write_text('#include <stdio.h>\n#include "report.h"\nint main(void){unsigned int w[256];while(fread(w,sizeof(w),1,stdin)==1)putchar(ownirq_report_valid(w,w[4],w[3])?\'1\':ownirq_evidence_valid(w,w[4],w[3])?\'R\':\'0\');return 0;}\n')
 subprocess.run([os.environ.get('CC','cc'),'-Wall','-Wextra','-fsanitize=address,undefined','-I'+str(HERE),str(source),'-o',str(exe)],check=True);return exe

def pack(w):return struct.pack('<256I',*w)

def main():
 with tempfile.TemporaryDirectory() as tmp:
  d=Path(tmp);exe=compile_gate(d);rows=[fixture(i) for i in range(1,6)]
  result=subprocess.check_output([str(exe)],input=b''.join(map(pack,rows)));assert result==b'1111R',result
  bad=[]
  for w in rows[:4]:
   for index in (2,17,18,19,20,22,23,24,26,27,31,32,34,40,44,51,53,54,88,170,247,249,250,251,252,253,254,255):
    x=w.copy();x[index]=0 if x[index] else 1;bad.append(x)
  assert subprocess.check_output([str(exe)],input=b''.join(map(pack,bad)))==b'0'*len(bad)
  payload=d/'payload';payload.write_bytes(bytes(4));build(d/'module',payload);s=(d/'module/stage_rehearsal.h').read_text()
  assert s.index('if(!valid)')<s.index('d->stop_clean=true;') and 'kmalloc(1024' in s
 print(f'OwnIRQ C gate: four cleanup fixtures, outstanding-reference refusal, {len(bad)} unsafe mutations rejected; ASan/UBSan passed.')
if __name__=='__main__':main()
