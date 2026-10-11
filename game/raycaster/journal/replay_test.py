#!/usr/bin/env python3
"""Convert a copy of existing evidence to journal format; this is NOT a live test."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from journal.metadata import Metadata
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--payload',type=Path,required=True);p.add_argument('--module',type=Path,required=True);a=p.parse_args()
with tempfile.TemporaryDirectory(prefix='i960-journal-replay-') as tmp:
    cap=Path(tmp)/'capture';shutil.copytree(a.capture.resolve(),cap,copy_function=lambda src,dst:os.symlink(src,dst))
    requests=json.loads((cap/'browser-requests.json').read_text());rows=json.loads((cap/'phases.json').read_text())
    cfg=json.loads((cap/'queue-test.json').read_text());cfg['metadata_format']='journal-v1'
    (cap/'queue-test.json').unlink();(cap/'queue-test.json').write_text(json.dumps(cfg))
    writer=Metadata(cap,'journal')
    for i,(label,data) in enumerate(requests):
        writer.intent(label,bytes.fromhex(data),requests[:i+1]);writer.result(rows[i],rows[:i+1])
    writer.finish(requests,rows,len(rows));writer.close()
    subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'browserqueue/tamper_test.py'),str(cap),'--payload',str(a.payload),'--module',str(a.module)],check=True)
