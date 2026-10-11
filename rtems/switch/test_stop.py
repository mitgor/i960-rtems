#!/usr/bin/env python3
"""Compile shared STOP1 handshake with ASan/UBSan; verify generated retention gates."""
import subprocess,tempfile,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as tmp:
 exe=Path(tmp)/'test'
 for source in ('test_stop.c','test_stop_target.c','test_cases.c'):
  subprocess.run(['clang','-std=gnu99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(HERE/source),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
 sys.path.insert(0,str(HERE));from build_stop_transport import build
 payload=Path(tmp)/'payload.bin';payload.write_bytes(bytes(4));out=Path(tmp)/'module';build(out,payload)
 s=(out/'dac960rtems.c').read_text();t=(out/'stage_rehearsal.h').read_text()
 assert 'd->stop_started=true;rc=stop_exchange(d)' in s
 assert 'if(d->stop_started&&!d->stop_clean)return -EBUSY;' in t
 assert t.index('rc=mu_cleanup(d,1,1)')<t.index('d->stop_clean=true;')
 assert 'slot==41 && d->stop_epoch' in s and 'static const u8 allowed[32]' in t
 print('STOP1 generation: exact-image pin and stop-before-reclaim retention gates passed')

with tempfile.TemporaryDirectory() as tmp:
 from build_cases_transport import build as build_cases
 payload=Path(tmp)/'payload.bin';payload.write_bytes(bytes(4));out=Path(tmp)/'module'
 build_cases(out,payload)
 s=(out/'stage_rehearsal.h').read_text()
 assert 'd->stop_case==4?16384u:0u' in s and 'd->stop_case==3?6u:0u' in s
 assert 'if(d->stop_started&&!d->stop_clean)return -EBUSY;' in s
 print('STOPCASE expected-outcome gates and cleanup retention generated correctly')
