#!/usr/bin/env python3
"""Generate the tested postboot validation module; no hardware access."""
from pathlib import Path
import argparse,shutil
from build import ROOT,HERE,replace

def build(out):
    out.mkdir(parents=True,exist_ok=False)
    for name in ['dac960dump.c','Makefile','rom_exec.h','staging_pointer.h','ram_scratch.h','stage_data.h']:
        shutil.copyfile(ROOT/'host/dump'/name,out/name)
    shutil.copyfile(HERE/'postboot_stage.h',out/'stage_rehearsal.h')
    p=out/'dac960dump.c';s=p.read_text()
    s=replace(s,'bool stage_armed, stage_dirty;','bool boot_verified;\n    bool stage_armed, stage_dirty;')
    s=replace(s,'if (opcode == 0x6f && (!d->exec_armed || !d->exec_dirty || count || offset))',
              'if (opcode == 0x6f && (!d->boot_verified || count || offset))')
    s=replace(s,'    if (d->pending) return -EPERM;',
              '    if (d->pending) return -EPERM;\n    if (opcode == 0x21) return -EPERM; /* postboot verification never uploads */')
    s=replace(s,'    if (strcmp(pci_name(pdev), bdf)) return -ENODEV;',
              '    if (strcmp(pci_name(pdev), bdf)) return -ENODEV;\n    if (!stage_check) return -EINVAL;')
    p.write_text(s)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args();build(args.out)
