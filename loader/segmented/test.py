#!/usr/bin/env python3
"""Native actual-core tests with ASan/UBSan; no hardware access."""
from pathlib import Path
import os, subprocess, tempfile
root=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as out:
 exe=Path(out)/'test'
 subprocess.run([os.environ.get('CC','cc'),'-std=c11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-fsanitize=address,undefined','-g',str(root/'arena.c'),str(root/'image.c'),str(root/'test_core.c'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
