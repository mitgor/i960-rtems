#!/usr/bin/env python3
import subprocess,tempfile
from pathlib import Path
r=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as d:
 t=Path(d)
 (t/'runtime_native.h').write_text('static unsigned runtime_lock(void){return 0;}\nstatic void runtime_unlock(unsigned v){(void)v;}\n')
 subprocess.run(['cc','-std=c11','-fsanitize=address,undefined','-g','-I'+str(t),str(r/'test_runtime.c'),str(r/'wire.c'),str(r/'../wad.c'),str(r/'../heap.c'),str(r/'../libc.c'),str(r/'../cache/cache.c'),str(r/'../../../../loader/segmented/arena.c'),'-o',str(t/'test')],check=True)
 subprocess.run([str(t/'test')],check=True)

with tempfile.TemporaryDirectory() as d:
 out=Path(d)/'wire'
 subprocess.run(['cc','-std=c11','-fsanitize=address,undefined','-g',str(r/'test_wire.c'),str(r/'wire.c'),'-o',str(out)],check=True)
 subprocess.run([str(out)],check=True)
