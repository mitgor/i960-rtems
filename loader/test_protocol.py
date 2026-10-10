#!/usr/bin/env python3
"""Compatibility entry point; the authoritative tests now execute the C code."""
import pathlib
import subprocess

if __name__ == '__main__':
    subprocess.run(['make', 'test'], cwd=pathlib.Path(__file__).resolve().parent, check=True)
