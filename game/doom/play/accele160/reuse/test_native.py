#!/usr/bin/env python3
"""Use the already linked host32 private engine; never touches card resources."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--platform',type=Path,required=True)
p.add_argument('--wad',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--sanitize',action='store_true')
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
here=Path(__file__).resolve().parent;root=here.parents[4]
engine=a.platform/'doom-platform.o';shared=a.out/'engine.so';exe=a.out/'reuse-native'
commands=[['gcc','-m32','-shared','-Wl,-z,notext','-o',str(shared),str(engine)],
          ['gcc','-m32','-O2','-funsigned-char','-fno-strict-aliasing','-no-pie',
           *(['-fsanitize=address,undefined','-fno-omit-frame-pointer','-g'] if a.sanitize else []),
           str(here/'native.c'),str(root/'game/doom/runtime/heap.c'),
           str(root/'loader/segmented/arena.c'),'-ldl','-o',str(exe)]]
with (a.out/'build.log').open('w') as log:
    for command in commands:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
run=subprocess.run([str(exe),str(shared.resolve()),str(a.wad)],capture_output=True,timeout=180)
(a.out/'stdout.txt').write_bytes(run.stdout);(a.out/'stderr.txt').write_bytes(run.stderr)
assert run.returncode==0,(run.returncode,run.stderr[-2000:])
assert b'PASS three fresh-image epochs' in run.stdout
report=dict(host_only=True,outer_runtime_sanitized=a.sanitize,engine_instrumented=False,cycles=3,same_process=True,same_arena=True,same_entry=True,
            engine_object_sha256=hashlib.sha256(engine.read_bytes()).hexdigest(),
            sources={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (here/'native.c',root/'game/doom/runtime/heap.c',root/'loader/segmented/arena.c')},
            commands=commands,stdout=run.stdout.decode())
(a.out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(run.stdout.decode())
