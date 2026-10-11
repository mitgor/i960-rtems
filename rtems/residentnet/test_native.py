#!/usr/bin/env python3
from pathlib import Path
import subprocess,tempfile
h=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'test';subprocess.run(['cc','-Wall','-Wextra','-Wno-unused-parameter','-Wno-unused-variable','-fsanitize=address,undefined','-g',str(h/'test_native.c'),'-o',str(p)],check=True);subprocess.run([str(p)],check=True)
