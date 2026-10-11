#!/usr/bin/env python3
import subprocess,tempfile
from pathlib import Path
from optimize import request_words,render_fast
HERE=Path(__file__).resolve().parent;GAME=HERE.parent;ROOT=GAME.parents[1]
with tempfile.TemporaryDirectory() as d:
 p=Path(d)
 (p/'fast.c').write_text('#define ray_size fast_size\n#define ray_request fast_request\n'+render_fast((GAME/'ray.c').read_text()))
 original=(ROOT/'rtems/transport/buffer_io.h').read_text()
 (p/'original_io.h').write_text(original);(p/'fast_io.h').write_text(request_words(original))
 subprocess.run(['cc','-std=c99','-O2','-fno-builtin','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-g','-I'+str(p),'-I'+str(GAME),str(GAME/'ray.c'),str(p/'fast.c'),str(HERE/'test.c'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
