#!/usr/bin/env python3
"""Opt-in hardware replay, fail-stop, preserving every capture in lossless archives."""
import argparse,hashlib,json,math,re,shutil,struct,subprocess,sys,time
from pathlib import Path
from tetris_wire import request,split
from capture_archive import pack

def next_request(state,index):
    if state is None or struct.unpack_from('<I',state,32)[0] or index%250==0:
        return 'init',request(seed=index+1)
    if index%127==126:return 'quit',request(state,key=ord('q'),ticks=0)
    key=ord('s') if index%11==0 else ord('w') if index%7==0 else ord('a') if index%3==0 else ord('d') if index%5==0 else 0
    return 'step',request(state,key=key,ticks=index%20+1)

def stats(values):
    values=sorted(values)
    return dict(min_ms=values[0]/1e6,median_ms=values[len(values)//2]/1e6,
                p95_ms=values[math.ceil(.95*len(values))-1]/1e6,max_ms=values[-1]/1e6,
                mean_ms=sum(values)/len(values)/1e6)

def run(a):
    if a.steps<1:raise ValueError('steps must be positive')
    base=a.baseline.read_bytes();a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'baseline.bin').write_bytes(base)
    (a.output/'archives').mkdir()
    metadata=dict(steps=a.steps,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                  payload_sha256=hashlib.sha256(a.payload.read_bytes()).hexdigest(),
                  module_sha256=hashlib.sha256(a.module.read_bytes()).hexdigest(),
                  oracle_sha256=hashlib.sha256(a.oracle.read_bytes()).hexdigest())
    (a.output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    rows=[];state=None;started=time.monotonic_ns()
    with (a.output/'progress.jsonl').open('x',buffering=1) as progress:
        for i in range(a.steps):
            kind,data=next_request(state,i);step_start=time.monotonic_ns()
            native=subprocess.run([str(a.oracle)],input=data,capture_output=True,check=True)
            inputfile=a.output/'next-request.bin';inputfile.write_bytes(data)
            capture=a.output/f'raw-{i:04d}'
            command=[sys.executable,str(Path(__file__).with_name('loadrun.py')),str(a.payload),'--module',str(a.module),
                     '--buffer-io','--input',str(inputfile),'--sequence',str(10001+i),'--expect','0','--output',str(capture)]
            call_start=time.monotonic_ns();proc=subprocess.run(command,capture_output=True,text=True);call_end=time.monotonic_ns()
            # Always save CLI output, even when probe insertion fails.
            (a.output/f'last-cli.txt').write_text(proc.stdout+proc.stderr)
            if proc.returncode:raise RuntimeError(f'step {i} loader failed; stop, do not retry: '+proc.stderr)
            response=(capture/'response.bin').read_bytes()
            if response!=native.stdout:raise RuntimeError(f'step {i} native/card mismatch')
            state,frame=split(response)
            (capture/'game-request.bin').write_bytes(data);(capture/'expected.bin').write_bytes(native.stdout)
            (capture/'cli.txt').write_text(proc.stdout+proc.stderr)
            log=(capture/'result.txt').read_text()
            times=re.search(r'TIMING setup_ns=(\d+) call_ns=(\d+) output_ns=(\d+) restore_ns=(\d+)',log)
            if not times or log.count('submit op=')!=128 or not (capture/'unloaded.txt').exists():raise RuntimeError('missing timing/command/unload evidence')
            if Path('/sys/module/dac960loadrun').exists() or Path('/sys/bus/pci/devices/0000:37:09.1/driver').exists():raise RuntimeError('card still owned')
            archive=a.output/'archives'/f'{i:04d}.zip'
            archive_start=time.monotonic_ns();pack(capture,archive,base)
            archive_end=time.monotonic_ns()
            # Delete only this run's raw files AFTER verified lossless round-trip.
            shutil.rmtree(capture)
            row=dict(index=i,kind=kind,sequence=10001+i,phase=struct.unpack_from('<I',state,32)[0],score=struct.unpack_from('<I',state,8)[0],
                     request_sha256=hashlib.sha256(data).hexdigest(),response_sha256=hashlib.sha256(response).hexdigest(),
                     cli_ns=call_end-call_start,archive_ns=archive_end-archive_start,step_ns=time.monotonic_ns()-step_start,
                     **dict(zip(['setup_ns','call_ns','output_ns','restore_ns'],map(int,times.groups()))))
            progress.write(json.dumps(row)+'\n');rows.append(row)
            (a.output/'latest-state.bin').write_bytes(state);(a.output/'latest-frame.txt').write_text(frame)
            if (i+1)%25==0 or i==0:print(f'{i+1}/{a.steps} exact matches; last CLI {row["cli_ns"]/1e6:.1f} ms',flush=True)
    summary=dict(completed=len(rows),elapsed_seconds=(time.monotonic_ns()-started)/1e9,
                 kinds={k:sum(r['kind']==k for r in rows) for k in ['init','step','quit']},
                 game_over_responses=sum(r['phase']==1 for r in rows),max_score=max(r['score'] for r in rows),
                 timings={key:stats([r[key] for r in rows]) for key in ['cli_ns','archive_ns','step_ns','setup_ns','call_ns','output_ns','restore_ns']})
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['payload','module','oracle','baseline','output']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--steps',type=int,default=1000)
    run(p.parse_args())
