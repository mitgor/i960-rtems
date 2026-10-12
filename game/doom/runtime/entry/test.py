#!/usr/bin/env python3
import subprocess,tempfile
from pathlib import Path
r=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'runtime_native.h').write_text('static unsigned runtime_lock(void){return 0;}\nstatic void runtime_unlock(unsigned v){(void)v;}\n')
 subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-g','-fsanitize=address,undefined','-I'+str(p),str(r/'test.c'),str(r/'../heap.c'),str(r/'../libc.c'),str(r/'../wad.c'),str(r/'../cache/cache.c'),str(r/'../../../../loader/segmented/arena.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
