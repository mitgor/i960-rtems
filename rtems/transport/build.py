#!/usr/bin/env python3
"""Derive a distinct, RAM-only RTEMS session transport; never change Tetris ABI."""
import argparse,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'host/loadrun'))
spec=importlib.util.spec_from_file_location('session_builder',ROOT/'host/session/build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from build import replace

def build(out):
 m.build(out)
 p=out/'buffer_io.h';s=p.read_text();s=s.replace('0xc0f34000u','0xc0f9c000u').replace('0x8000u','0x70000u').replace('0x314f4942u','0x314f4952u')
 s=replace(s,'        if(before[i]!=after[i]) return 0;','''        /* Explicit RTEMS private data/workspace. Guard words remain immutable. */
        if(i>=0x20010u && i<0x6fff0u) continue;
        if(before[i]!=after[i]) return 0;''')
 p.write_text(s)
 p=out/'load_policy.h';s=p.read_text().replace('#define LOAD_MAX 0x10000u','#define LOAD_MAX 0x73060u');p.write_text(s)
 p=out/'dac960session.c';s=p.read_text().replace('dac960session','dac960rtems').replace('i960-session','i960-rtems').replace('entry_offset >= BIO_OFFSET','entry_offset >= 0x20000u')
 (out/'dac960rtems.c').write_text(s);p.unlink()
 p=out/'Makefile';p.write_text(p.read_text().replace('dac960session','dac960rtems'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);build(p.parse_args().out)
