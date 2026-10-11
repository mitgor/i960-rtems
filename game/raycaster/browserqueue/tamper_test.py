#!/usr/bin/env python3
"""Reject corrupted browser captures without modifying the physical originals."""
import argparse
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--payload',type=Path,required=True);p.add_argument('--module',type=Path,required=True);a=p.parse_args()
script=Path(__file__).with_name('verify.py')
def check(cap):
    return subprocess.run([sys.executable,str(script),str(cap),'--payload',str(a.payload.resolve()),'--module',str(a.module.resolve())],capture_output=True,text=True)
assert check(a.capture).returncode==0,'original must pass before mutation tests'
mutations=['request','label','profile','command-log','full-immutable','full-queue','payload-hash','restoration']
journal=(a.capture/'metadata-journal.jsonl').exists()
if journal:mutations+=['journal-missing','journal-truncated','journal-unsealed','journal-chain']
for kind in mutations:
    with tempfile.TemporaryDirectory(prefix='i960-browser-tamper-') as tmp:
        cap=Path(tmp)/'capture'
        shutil.copytree(a.capture.resolve(),cap,copy_function=lambda src,dst:os.symlink(src,dst))
        def replace(name,data):
            path=cap/name;path.unlink();path.write_bytes(data)
        if kind in ('request','label'):
            rows=json.loads((cap/'browser-requests.json').read_text())
            if kind=='label':rows[0][0]='browser-combined'
            else:
                req=bytearray.fromhex(rows[0][1]);req[8:12]=bytes(4);rows[0][1]=req.hex()
            replace('browser-requests.json',json.dumps(rows).encode())
        elif kind=='profile':
            rows=json.loads((cap/'phases.json').read_text());rows[0]['audit_bytes']=1
            replace('phases.json',json.dumps(rows).encode())
        elif kind=='command-log':
            rows=gzip.decompress((cap/'commands.jsonl.gz').read_bytes()).decode().splitlines()
            row=json.loads(rows[0]);row['commands'].pop();rows[0]=json.dumps(row)
            replace('commands.jsonl.gz',gzip.compress(('\n'.join(rows)+'\n').encode()))
        elif kind.startswith('full-'):
            source=cap/'full-audits.bin.gz';original=source.resolve();source.unlink()
            with gzip.open(original,'rb') as inp,gzip.open(source,'wb') as out:
                first=bytearray(inp.read(524288));first[0 if kind=='full-immutable' else 0x60000]^=1;out.write(first)
                shutil.copyfileobj(inp,out)
        elif kind.startswith('journal-'):
            name='metadata-journal.jsonl';data=(cap/name).read_bytes()
            if kind=='journal-missing':(cap/name).unlink()
            elif kind=='journal-truncated':replace(name,data[:-1])
            elif kind=='journal-unsealed':replace(name,b'\n'.join(data.splitlines()[:-1])+b'\n')
            else:
                lines=data.splitlines();row=json.loads(lines[1]);row[1]='f'*64
                lines[1]=json.dumps(row,sort_keys=True,separators=(',',':')).encode()
                replace(name,b'\n'.join(lines)+b'\n')
        else:
            name='request.json' if kind=='payload-hash' else 'summary.json'
            row=json.loads((cap/name).read_text())
            row['payload_sha256' if kind=='payload-hash' else 'restored']='0'*64 if kind=='payload-hash' else False
            replace(name,json.dumps(row).encode())
        result=check(cap)
        assert result.returncode!=0,(kind,'corruption accepted')
        expected='ValueError: program modified immutable bytes or output guards' if kind=='full-immutable' else 'AssertionError'
        if journal and kind in ('request','label','profile'):expected='ValueError: journal/export mismatch'
        if kind.startswith('journal-'):expected='FileNotFoundError' if kind=='journal-missing' else 'ValueError:'
        assert expected in result.stderr,(kind,result.stderr)
print(json.dumps(dict(original_accepted=True,rejected=mutations),indent=2))
