#!/usr/bin/env python3
import subprocess,tempfile
from pathlib import Path
from test_generated import check
HERE=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as d:
 p=Path(d)
 subprocess.run(['cc','-O2','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(HERE),str(HERE/'test_transport.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
 for queue in [False,True]:
  out=p/str(queue);subprocess.run(['python3',str(HERE/'build_transport.py'),'--out',str(out),*(['--queue'] if queue else [])],check=True)
  s=(out/'stage_rehearsal.h').read_text();assert 'd->output_length=IMAGE_WINDOW;' in s
  if queue:
   # The new read is before, and never replaces, the original full audit.
   start=s.index('qrc=fq_targeted(d)');audit=s.index('rc=session_output(d,d->output_length)',start)
   assert start<s.index('if(d->pending)return qrc',start)<audit<s.index('if(qrc)return qrc',audit)<s.index('rc=fq_match_audit(d)',audit)
   check(out,p)
   driver=(out/'dac960rtems.c').read_text();assert 'capture[60]' in driver and 'if(i>=54)d->capture[i].blob.size=i<56?64:FQ_SLOT_SIZE;' in driver
 print('PASS: full audit every STEP; no additional submission after uncertain completion; fixed capture allocation sizes')
