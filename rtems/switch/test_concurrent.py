#!/usr/bin/env python3
import subprocess,tempfile
from pathlib import Path
from build_concurrent_transport import build
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as tmp:
 exe=Path(tmp)/'test'
 subprocess.run(['clang','-std=gnu11','-Wall','-Wextra','-Werror','-pthread','-fsanitize=address,undefined',str(here/'test_concurrent.c'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
 payload=Path(tmp)/'payload';payload.write_bytes(bytes(4));out=Path(tmp)/'module';build(out,payload)
 s=(out/'dac960rtems.c').read_text();t=(out/'stage_rehearsal.h').read_text()
 assert s.index('d->control_window=false')<s.index('returned = readw')
 assert 'mutex_lock(&d->session_lock);' not in s[s.index('static long concurrent_ioctl'):s.index('static int issue')]
 assert 'if(d->stop_started&&!d->stop_clean)return -EBUSY;' in t
 assert 'static const u8 allowed[32]' in t
 print('Generated concurrent driver: join-before-completion, no inverse lock acquisition, pinned image and retention gates passed')
