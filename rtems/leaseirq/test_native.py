#!/usr/bin/env python3
"""Lease deadline/sequence oracle, report rejection, and host ownership guards."""
import importlib.util,os,struct,subprocess,tempfile
from pathlib import Path
from build_transport import build
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('persist_tests',HERE.parent/'persistirq/test_native.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
def compile_gate(d):
 (d/'persist_report.h').write_text((HERE.parent/'persistirq/report.h').read_text());(d/'lease_report.h').write_text((HERE/'report.h').read_text())
 src=d/'gate.c';src.write_text('#include <stdio.h>\n#include "lease_report.h"\nint main(void){unsigned int w[352];while(fread(w,sizeof(w),1,stdin)==1)putchar(lease_valid(w,w[4],w[3])?\'1\':\'0\');return 0;}\n');exe=d/'gate'
 subprocess.run([os.environ.get('CC','cc'),'-Wall','-Wextra','-fsanitize=address,undefined',str(src),'-o',str(exe)],check=True);return exe
def fixture():
 w=base.fixture();w[317]=0;w += [0x3145534c,1,3,1,18,18,0,0,0,1,50,0,0x2000,0xf80000,0xc0100020,w[26],20000,0,0,0x6000,0xc0f2c000,0xc0f9bff0,0x1fb,0xff,24000,512,17,18,1,15,0,0];return w
def main():
 with tempfile.TemporaryDirectory() as tmp:
  d=Path(tmp);src=d/'policy.c';src.write_text('''#include <stdio.h>
#include "lease.h"
int main(void){unsigned int epoch,tick,token,init,ack;struct execution_lease l;
while(scanf("%u%u%u%u",&init,&epoch,&tick,&token)==4){if(init)lease_init(&l,epoch,tick);ack=lease_poll(&l,tick,token);printf("%u %u %u %u %u %u %u %u %u %u %u\\n",ack,l.state,l.start,l.grant,l.last,l.seq,l.seen,l.reason,l.stop,l.maxgap,l.rejects);}return 0;}
''');exe=d/'policy';subprocess.run(['cc','-Wall','-Wextra','-fsanitize=address,undefined','-I'+str(HERE),str(src),'-o',str(exe)],check=True)
  lines=[];expected=[]
  # Independent integer model includes stale/skipped sequences, exact deadline,
  # no-grant expiry, late STOP, tick wrap, and the non-renewable administrative cap.
  cases=0
  for start in (0,123,0xffffff00):
   for grant in (False,True):
    for renewgap in (1,511,512,513):
     state=dict(state=1,start=start,grant=0,last=start,seq=0,seen=0,reason=0,stop=0,maxgap=0,rejects=0)
     schedule=[(0,0),(1,0x61000009 if grant else 0x61000008),(2,0x63000002),(3,0x63000001),(4,0x63000001),(renewgap+3,0x63000002),(renewgap+4,0x72000009),(renewgap+520,0x63000003)]
     schedule.sort(key=lambda x:x[0])
     for n,(delta,token) in enumerate(schedule):
      tick=(start+delta)&0xffffffff;ack=0;l=state
      if l['state']!=3:
       gap=(tick-l['last'])&0xffffffff;l['maxgap']=max(l['maxgap'],gap)
       if ((tick-l['start'])&0xffffffff)>=24000 or gap>=512:l.update(state=3,reason=3 if ((tick-l['start'])&0xffffffff)>=24000 else 2,stop=tick)
       elif token!=l['seen']:
        l['seen']=token
        if token==0x61000009 and l['state']==1:l.update(state=2,grant=tick,last=tick);ack=0x62000009
        elif token>>16==0x6300 and l['state']==2 and token&65535==l['seq']+1 and token&65535:l.update(seq=token&65535,last=tick);ack=0x64000000|(token&65535)
        elif token==0x72000009 and l['state']==2:l.update(state=3,reason=1,stop=tick)
        elif token:l['rejects']+=1
      lines.append(f'{int(n==0)} 9 {tick} {token}');expected.append(' '.join(map(str,[ack,*[l[k] for k in ('state','start','grant','last','seq','seen','reason','stop','maxgap','rejects')]])));cases+=1
  assert subprocess.check_output([str(exe)],input=('\n'.join(lines)+'\n').encode()).decode().splitlines()==expected
  # Renew through the administrative limit: renewal cannot extend the cap.
  extra=['1 9 0 0','0 9 1 1627389961']+[f'0 9 {i*400} {0x63000000+i}' for i in range(1,61)]
  last=subprocess.check_output([str(exe)],input=('\n'.join(extra)+'\n').encode()).decode().splitlines()[-1].split();assert last[1]=='3' and last[7]=='3' and last[8]=='24000'
  gate=compile_gate(d);w=fixture();pack=lambda x:struct.pack('<352I',*x);assert subprocess.check_output([str(gate)],input=pack(w))==b'1'
  bad=[]
  for i in (320,321,322,323,324,325,327,328,329,330,331,332,333,334,335,336,337,339,340,341,342,343,344,345,346,347,348,349,350,351):
   x=w.copy();x[i]=0 if x[i] else 1;bad.append(pack(x))
  # maxgap zero is legal when grant and STOP land on the same tick; fixture is 1.
  bad.pop(8)
  assert subprocess.check_output([str(gate)],input=b''.join(bad))==b'0'*len(bad)
  payload=d/'payload';payload.write_bytes(bytes(4));build(d/'module',payload)
  s=(d/'module/dac960rtems.c').read_text();assert '(opcode==0x6f && slot==41 && d->stop_epoch)?125000000u:WAIT_US' in s and 'no stock commands until RELEASE' in s
 print(f'Lease: {cases} modeled transitions, deadline/cap/wrap cases, {len(bad)} hardware report corruptions, pinned module guards passed under ASan/UBSan.')
if __name__=='__main__':main()
