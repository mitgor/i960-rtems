#!/usr/bin/env python3
"""Check both firmware entry/runtime use one bounded session policy."""
import subprocess,tempfile
from pathlib import Path
r=Path(__file__).resolve().parents[1]
for name in ('app.c','runtime.c'):
 text=(r/'exclusive'/name).read_text()
 assert '#include "session_limit.h"' in text and '#define EXCLUSIVE_MAX_TICKS' not in text
cases=[([],6000),(['I960_RESIDENT_NET'],180000),(['I960_RESIDENT_NET','I960_OWNED_MIB=12'],360000),(['I960_RESIDENT_NET','I960_OWNED_MIB=12','I960_DOOM_STARTUP'],540000)]
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'limit.c'
 for flags,expected in cases:
  p.write_text('#include "session_limit.h"\ntypedef char correct[(EXCLUSIVE_MAX_TICKS=='+str(expected)+'u && EXCLUSIVE_MAX_TICKS<0x1000000u)?1:-1];\n')
  subprocess.run(['cc','-fsyntax-only','-I'+str(r/'exclusive'),*['-D'+f for f in flags],str(p)],check=True)
 for flags in (['I960_DOOM_STARTUP'],['I960_RESIDENT_NET','I960_OWNED_MIB=10','I960_DOOM_STARTUP']):
  run=subprocess.run(['cc','-fsyntax-only','-I'+str(r/'exclusive'),*['-D'+f for f in flags],str(p)],capture_output=True)
  assert run.returncode!=0
print('PASS shared firmware limits: 1/30/60/90 minutes, ARM word fits, invalid startup configurations refused')
