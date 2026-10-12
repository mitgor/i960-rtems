#!/usr/bin/env python3
import subprocess,tempfile
from pathlib import Path
r=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as tmp:
 out=Path(tmp)/'cache-test'
 subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-fsanitize=address,undefined','-g',str(r/'cache.c'),str(r/'test.c'),'-o',str(out)],check=True)
 subprocess.run([str(out)],check=True)

with tempfile.TemporaryDirectory() as tmp:
 out=Path(tmp)/'backend-test'
 # Only the public Doom WAD interface is mocked; real engine builds also use
 # this same backend against the pinned upstream header.
 (Path(tmp)/'w_file.h').write_text('#include <stddef.h>\ntypedef struct wad_file_s wad_file_t; typedef struct {wad_file_t*(*OpenFile)(char*);void(*CloseFile)(wad_file_t*);size_t(*Read)(wad_file_t*,unsigned,void*,size_t);}wad_file_class_t;struct wad_file_s{wad_file_class_t*file_class;unsigned char*mapped;unsigned length;};\n')
 subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-fsanitize=address,undefined','-g','-I'+tmp,str(r/'cache.c'),str(r/'backend.c'),str(r/'test_backend.c'),'-o',str(out)],check=True)
 subprocess.run([str(out)],check=True)
