#!/usr/bin/env python3
"""Compile and exercise the shared IRQ continuation lifetime policy without hardware."""
import os
import subprocess
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory(prefix="i960-irq-lifetime-") as tmp:
    binary = Path(tmp) / "test-lifetime"
    subprocess.run([os.environ.get("CC", "cc"), "-std=c99", "-Wall", "-Wextra",
                    "-Werror", "-fsanitize=address,undefined", "-g",
                    str(Path(__file__).with_suffix(".c")), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
