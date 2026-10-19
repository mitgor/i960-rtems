#!/usr/bin/env python3
import subprocess,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent;root=here.parents[2];seg=root/'loader/segmented'
with tempfile.TemporaryDirectory() as tmp:
 exe=Path(tmp)/'test'
 subprocess.run(['cc','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-fsanitize=address,undefined','-I'+str(seg),str(here/'runtime.c'),str(here/'test_runtime.c'),str(seg/'arena.c'),str(seg/'image.c'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)

with tempfile.TemporaryDirectory() as tmp:
 exe=Path(tmp)/'card'
 subprocess.run(['cc','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-fsanitize=address,undefined','-I'+str(seg),str(here/'runtime.c'),str(here/'test_card.c'),str(seg/'arena.c'),str(seg/'image.c'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
