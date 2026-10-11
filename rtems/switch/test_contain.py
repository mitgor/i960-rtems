#!/usr/bin/env python3
"""Corrupt reclaim-critical evidence; exercise the exact C gate under sanitizers."""
import os,struct,subprocess,tempfile
from pathlib import Path
from live_contain import decode
from build_contain_transport import build
HERE=Path(__file__).resolve().parent

def fixture():
 w=[0]*236
 w[:20]=[0x31575349,0,40,30,30,0,0,1,1,0,0,0x10c7,0x80000,0x1234,0x1234,0,0,0,0,0]
 for i in range(2):
  n=20+i*82;base=0x10000+i*0x4000;irq=0x30000+i*0x4000
  w[n:n+12]=[0x100+i*4,base,base+8192,base+256,0x142002,0,0xf2,1,20,19,irq,irq+256]
  w[n+12:n+27]=[0x19600000+i*0x10000000+j for j in range(15)];w[n+81]=800000
 w[184:204]=[0x31505453,123,8,36,0x100,1,1,1,1,40,19,19,500,0x4d554f4b,0,0,0,0,0,0]
 w[204:]=[0x314e5443,0x200,36,40,4,900000,900000,800000,800000,800000,800000,2,2,2,2,0x200,0x200,10000,123,456,123,456,789,1234,789,1234,0x514f4b31,1,0,0,0,0]
 return w

def main():
 w=fixture();raw=struct.pack('<236I',*w);decode(raw)
 changes={i:1 for i in (1,5,6,9,10,15,16,17,19)}
 changes.update({i:0 for i in (0,2,3,4,7,8,11,12,184,185,186,187,188,189,190,191,192,193,196,197)})
 changes[18]=0x2000;changes[13]=0
 changes.update({i:1 for i in range(198,204)})
 for i in range(204,236):changes[i]=1 if w[i]==0 else 0
 for n in (20,102):
  changes.update({n+i:0 for i in (0,2,3,6,7,8,11,12,81)})
  changes[n+9]=20;changes[n+80]=1
 samples=[raw]
 for i,value in changes.items():
  bad=w.copy();bad[i]=value;b=struct.pack('<236I',*bad)
  try:decode(b)
  except AssertionError:pass
  else:raise AssertionError(('Python accepted damaged report',i))
  samples.append(b)
 with tempfile.TemporaryDirectory() as tmp:
  d=Path(tmp);c=d/'check.c';exe=d/'check'
  c.write_text('#include <stdio.h>\n#include "contain_report.h"\nint main(void){unsigned int w[236];while(fread(w,sizeof(w),1,stdin)==1)putchar(contain_report_valid(w,123)?\'1\':\'0\');return 0;}\n')
  subprocess.run([os.environ.get('CC','cc'),'-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(HERE),str(c),'-o',str(exe)],check=True)
  result=subprocess.check_output([str(exe)],input=b''.join(samples));assert result==b'1'+b'0'*len(changes),result
  payload=d/'payload';payload.write_bytes(bytes(4));out=d/'module';build(out,payload)
  s=(out/'stage_rehearsal.h').read_text();driver=(out/'dac960rtems.c').read_text()
  assert s.index('if(!contain_report_valid(words,d->stop_epoch))return -ENODATA;')<s.index('d->stop_clean=true;')
  assert 'if(d->stop_started&&!d->stop_clean)return -EBUSY;' in s
  assert '0x75000000u|d->control_epoch' in driver and 'CONCURRENT DRAINED ioctl' not in driver
 print(f'Containment: exact C gate ASan/UBSan and Python reject {len(changes)} damaged reports; pinned QUIESCED protocol and pre-cleanup gate verified')
if __name__=='__main__':main()
