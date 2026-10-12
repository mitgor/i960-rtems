#!/usr/bin/env python3
import os,subprocess,tempfile
from pathlib import Path
r=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as tmp:
 out=Path(tmp)/'test'
 command=[os.environ.get('CC','cc'),'-std=c99','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-g','-fsanitize=address,undefined',str(r/'heap.c'),str(r/'../../../loader/segmented/arena.c'),str(r/'test_heap.c'),'-o',str(out)]
 subprocess.run(command,check=True);subprocess.run([str(out)],check=True)
