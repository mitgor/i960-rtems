#!/usr/bin/env python3
"""Native sanitizer tests, optional cross-build/interpreter equivalence checks."""
import argparse
from pathlib import Path
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[2]

def command(args):
    r=subprocess.run([str(x) for x in args],capture_output=True,text=True)
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    return r.stdout.strip()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cross',help='cross-tool prefix, e.g. /home/mit/i960/tools/bin/i960-coff-')
    a=p.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        d=Path(tmp);game=ROOT/'game/tetris'
        result=command(['cc','-O1','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-DTETRIS_CORE_ONLY',game/'tetris.c',game/'test_tetris.c','-o',d/'native'])
        native=command([d/'native']);assert native.startswith('RESULT=') and int(native.split('=')[1])>0,native
        print('Native ASan/UBSan: '+native)
        if a.cross:
            for src,out,flag in [('tetris.c','core.o','TETRIS_CORE_ONLY'),('test_tetris.c','test.o','TARGET_I960')]:
                command([a.cross+'gcc','-mrp','-O2','-ffreestanding','-fno-builtin','-D'+flag,'-c',game/src,'-o',d/out])
            command([a.cross+'ld','-T',game/'i960.ld',d/'core.o',d/'test.o','-o',d/'test.elf'])
            command(['cc','-O2',ROOT/'host/emu.c','-o',d/'emu'])
            target=command([d/'emu','-t',d/'test.elf']);assert target==native,(native,target)
            print('i960 interpreter: '+target+' (1024 state/frame transitions plus rule tests)')
            command([a.cross+'gcc','-mrp','-c',ROOT/'host/test_setbit.s','-o',d/'setbit.o'])
            command([a.cross+'ld','-T',game/'i960.ld',d/'setbit.o','-o',d/'setbit.elf'])
            assert command([d/'emu','-t',d/'setbit.elf'])=='RESULT=-2147483389'
            (d/'bad.s').write_text('.text\n.globl _main\n_main:\n.word 0\n')
            command([a.cross+'gcc','-mrp','-c',d/'bad.s','-o',d/'bad.o'])
            command([a.cross+'ld','-T',game/'i960.ld',d/'bad.o','-o',d/'bad.elf'])
            bad=subprocess.run([str(d/'emu'),'-t',str(d/'bad.elf')],capture_output=True,text=True)
            assert bad.returncode!=0 and 'unimpl' in bad.stderr
            print('setbit literal/register/modulo/bit31 and unsupported-instruction exit: passed')
if __name__=='__main__':main()
