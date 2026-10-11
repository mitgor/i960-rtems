#!/usr/bin/env python3
import os,subprocess,tempfile
from pathlib import Path
from build_transport import build
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as tmp:
 d=Path(tmp);exe=d/'test'
 subprocess.run([os.environ.get('CC','cc'),'-std=c99','-Wall','-Wextra','-fsanitize=address,undefined',str(here/'test_policy.c'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
 p=d/'payload';p.write_bytes(bytes(4));build(d/'module',p)
 s=(d/'module/stage_rehearsal.h').read_text()
 assert s.index('if(d->ownership_open)')<s.index('if(d->pending || d->runner_uncertain)')
 assert s.index('if(!ownership_report_valid')<s.index('d->ownership_open=false')
print('Ownership policy: 1000 lease/cancel/restart epochs; stale/duplicate references and quarantine reuse rejected; terminal report gates ASan/UBSan passed')
