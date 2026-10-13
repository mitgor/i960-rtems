#!/usr/bin/env python3
"""Recheck saved T2 runs against freshly compiled native game; no card access."""
import hashlib,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'host/loadrun'))
from loadrun import verify
from tetris_wire import split

def main():
    base=ROOT/'artifacts/tetris-t2-20261010/acceptance';rows=[]
    with tempfile.TemporaryDirectory() as tmp:
        oracle=Path(tmp)/'oracle'
        subprocess.run(['cc','-O2','-std=c99','-Wall','-Wextra','-Werror','-DTETRIS_CORE_ONLY',str(ROOT/'game/tetris/tetris.c'),str(ROOT/'game/tetris/oracle.c'),'-o',str(oracle)],check=True)
        for p in sorted(base.glob('run-*')):
            name=p.name[4:];data=(base/(name+'-request.bin')).read_bytes()
            ref=subprocess.run([str(oracle)],input=data,capture_output=True)
            status=json.loads((p/'response.json').read_text())['status']
            assert ref.returncode==status
            assert verify(p,(p/'payload.bin').read_bytes())==0
            output=(p/'response.bin').read_bytes();assert ref.stdout==output
            assert (p/'unloaded.txt').exists()
            if status==0:
                state,frame=split(output)
                assert (p/'state.bin').read_bytes()==state
                assert (p/'frame.txt').read_text()==frame
            rows.append(dict(run=name,status=status,bytes=len(output),sha256=hashlib.sha256(output).hexdigest()))
        assert len(rows)==9
    print(json.dumps(dict(validated=True,runs=rows),indent=2))
if __name__=='__main__':main()
