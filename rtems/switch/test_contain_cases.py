#!/usr/bin/env python3
import os,struct,subprocess,tempfile
from pathlib import Path
from test_contain import fixture
from live_contain_cases import decode
from build_contain_cases import report_header,build
samples=[];expected=[];badcount=0
for mode in (1,2):
 w=fixture()+[0]*20;w[2]=44;w[186]=17 if mode==1 else 29;w[187]=w[186]+1;w[191]=4-mode;w[193]=44;w[206]=40;w[207]=44
 w[236:]=[mode,16,28,40,41,2,1,1,0,8,8,40,0,12,12,0,24,mode,0,0]
 b=struct.pack('<256I',*w);decode(b);samples.append(b);expected.append(1)
 for i in range(236,256):
  bad=w.copy();bad[i]=0 if w[i] else 1
  b=struct.pack('<256I',*bad)
  try:decode(b)
  except AssertionError:pass
  else:raise AssertionError(i)
  samples.append(b);expected.append(0);badcount+=1
with tempfile.TemporaryDirectory() as tmp:
 d=Path(tmp);(d/'gate.h').write_text(report_header());(d/'test.c').write_text('#include <stdio.h>\n#include "gate.h"\nint main(void){unsigned int w[256];while(fread(w,sizeof(w),1,stdin)==1)putchar(contain_cases_valid(w,123,w[236])?\'1\':\'0\');return 0;}')
 subprocess.run([os.environ.get('CC','cc'),'-fsanitize=address,undefined',str(d/'test.c'),'-o',str(d/'test')],check=True)
 assert subprocess.check_output([str(d/'test')],input=b''.join(samples))==bytes(48+x for x in expected)
 payload=d/'payload';payload.write_bytes(bytes(4));build(d/'module',payload)
 assert 'contain_cases_valid(words,d->stop_epoch,d->contain_case)' in (d/'module/stage_rehearsal.h').read_text()
print(f'Critical containment: both modes pass; C ASan/UBSan and Python reject {badcount} damaged critical reports')
