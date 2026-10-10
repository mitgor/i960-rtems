#!/usr/bin/env python3
"""Explicit opt-in live T2 acceptance runner; not a unittest discovery test.
Requires root, the exact known loader module, and a native oracle executable.
Stops on first failed transaction or byte mismatch. Never retries execution.
"""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from tetris_wire import request,split

def run(a):
    a.output.mkdir(parents=True,exist_ok=False)
    state=None;rows=[]
    for index,name in enumerate(['init','left','rotate','drop','quit','restart','two-lines','game-over','bad-ticks']):
        if name in ('init','restart'):data=request(seed=1)
        elif name=='two-lines':
            s=bytearray(state)
            import struct
            struct.pack_into('<10I',s,0,1,1,0,1,0,3,18,19,0,0)
            s[40:]=bytes(200)
            for r in (18,19):
                for c in range(10):s[40+r*10+c]=0 if c in (4,5) else ord('J')
            s[40+17*10]=ord('L');data=request(s,ticks=1)
        elif name=='game-over':
            s=bytearray(state)
            import struct
            struct.pack_into('<10I',s,0,1,1,0,0,0,3,18,19,0,0);s[40:]=bytes(200)
            for r in (0,1):
                for c in range(3,7):s[40+r*10+c]=ord('J')
            data=request(s,ticks=1)
        elif name=='bad-ticks':
            import struct
            data=bytearray(request(state));struct.pack_into('<I',data,12,21);data=bytes(data)
        else:data=request(state,key=ord(dict(left='a',rotate='w',drop='s',quit='q')[name]),ticks=20 if name=='drop' else 1)
        native=subprocess.run([str(a.oracle)],input=data,capture_output=True)
        expected_status=1 if name=='bad-ticks' else 0
        if native.returncode!=expected_status:raise RuntimeError('native reference failed: '+name)
        inputfile=a.output/(name+'-request.bin');inputfile.write_bytes(data)
        capture=a.output/('run-'+name)
        command=[sys.executable,str(Path(__file__).with_name('loadrun.py')),str(a.payload),'--module',str(a.module),
                 '--buffer-io','--input',str(inputfile),'--sequence',str(2001+index),'--expect','0','--output',str(capture)]
        proc=subprocess.run(command,capture_output=True,text=True)
        (a.output/(name+'-cli.txt')).write_text(proc.stdout+proc.stderr)
        if not (capture/'unloaded.txt').exists():raise RuntimeError('module did not unload: '+name)
        meta=json.loads((capture/'response.json').read_text())
        if proc.returncode!=expected_status or meta['status']!=expected_status:raise RuntimeError('unexpected target status: '+name)
        output=(capture/'response.bin').read_bytes()
        if output!=native.stdout:raise RuntimeError('native/card byte mismatch: '+name)
        if not expected_status:
            state,frame=split(output)
            (capture/'state.bin').write_bytes(state);(capture/'frame.txt').write_text(frame)
            (capture/'expected.bin').write_bytes(native.stdout)
        rows.append(dict(name=name,status=meta['status'],bytes=len(output),sha256=hashlib.sha256(output).hexdigest()))
        print(name+': exact native/card match',flush=True)
    (a.output/'validation.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('payload','module','oracle','output'):p.add_argument('--'+name,type=Path,required=True)
    run(p.parse_args())
