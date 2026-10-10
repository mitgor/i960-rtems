#!/usr/bin/env python3
"""Reconstruct and independently verify a saved replay; no hardware access."""
import argparse,hashlib,json,re,struct,subprocess
from pathlib import Path
from capture_archive import read
from loadrun import verify,ROM_SHA
from tetris_replay import next_request,stats
from tetris_wire import split

class Capture:
    def __init__(self,files,name=''):self.files,self.name=files,name
    def __truediv__(self,name):return Capture(self.files,name)
    def read_bytes(self):return self.files[self.name]
    def read_text(self):return self.read_bytes().decode()

def validate(folder,oracle):
    base=(folder/'baseline.bin').read_bytes()
    if hashlib.sha256(base).hexdigest()!=ROM_SHA:raise ValueError('wrong baseline')
    meta=json.loads((folder/'metadata.json').read_text())
    rows=[json.loads(line) for line in (folder/'progress.jsonl').read_text().splitlines()]
    if len(rows)!=meta['steps']:raise ValueError('incomplete replay')
    state=None;total=0;chain=hashlib.sha256()
    for index,row in enumerate(rows):
        if row['index']!=index:raise ValueError('sequence gap')
        files=read(folder/'archives'/f'{index:04d}.zip',base)
        kind,data=next_request(state,index)
        if files['game-request.bin']!=data or row['kind']!=kind:raise ValueError('replay continuity mismatch')
        req=json.loads(files['request.json'])
        if req['boot_id']!=meta['boot_id'] or req['module_sha256']!=meta['module_sha256']:raise ValueError('provenance changed')
        if verify(Capture(files),files['payload.bin'])!=0:raise ValueError('bad scalar return')
        response=files['response.bin'];expected=subprocess.run([str(oracle)],input=data,capture_output=True,check=True).stdout
        if response!=expected or files['expected.bin']!=expected:raise ValueError('native mismatch')
        state,frame=split(response)
        info=json.loads(files['response.json'])
        if info!=dict(status=0,length=2160,sequence=10001+index):raise ValueError('wrong response metadata')
        if row['response_sha256']!=hashlib.sha256(response).hexdigest() or row['request_sha256']!=hashlib.sha256(data).hexdigest():raise ValueError('row hash mismatch')
        if row['phase']!=struct.unpack_from('<I',state,32)[0] or row['score']!=struct.unpack_from('<I',state,8)[0]:raise ValueError('state metadata mismatch')
        log=files['result.txt'].decode();count=log.count('submit op=');total+=count
        submissions=re.findall(r'^submit op=([0-9a-f]+) id=(\d+) ',log,re.M)
        completions=re.findall(r'^complete op=([0-9a-f]+) id=([0-9a-f]+) status=([0-9a-f]+) .*?guard-changed=(\d+)',log,re.M)
        if len(submissions)!=128 or len(completions)!=128:raise ValueError('missing completions')
        for (op,ident),(done_op,done_id,status,guard) in zip(submissions,completions):
            if op!=done_op or int(ident)!=int(done_id,16) or int(guard):raise ValueError('ID/guard mismatch')
            allowed=(0x17d,0x17e,0x17f) if op=='6f' else (0,)
            if int(status,16) not in allowed:raise ValueError('unexpected completion status')
        if sum(int(c[2],16)==0x17f for c in completions)!=1:raise ValueError('wrong execution count')
        if count!=128 or 'unloaded.txt' not in files:raise ValueError('incomplete transaction')
        timing=re.search(r'TIMING setup_ns=(\d+) call_ns=(\d+) output_ns=(\d+) restore_ns=(\d+)',log)
        if not timing or list(map(int,timing.groups()))!=[row[k] for k in ['setup_ns','call_ns','output_ns','restore_ns']]:raise ValueError('timing mismatch')
        chain.update(data);chain.update(response)
    return dict(validated=True,transactions=len(rows),firmware_commands=total,boot_id=meta['boot_id'],
                request_response_chain_sha256=chain.hexdigest(),timings={k:stats([r[k] for r in rows]) for k in ['cli_ns','setup_ns','call_ns','output_ns','restore_ns']})
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);p.add_argument('--oracle',required=True,type=Path)
    a=p.parse_args();print(json.dumps(validate(a.folder,a.oracle),indent=2))
