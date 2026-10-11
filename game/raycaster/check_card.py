#!/usr/bin/env python3
import argparse,json,re,time
from pathlib import Path
from host import Native,card_backend,request,decode
p=argparse.ArgumentParser();p.add_argument('--payload',type=Path,required=True);p.add_argument('--module',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
oracle=Native();board=card_backend(a.payload,a.module,a.output);rows=[]
def step(label,data):
 start=time.monotonic_ns();reply=board.step(data);end=time.monotonic_ns()
 assert reply==oracle.step(data),label
 log=board.debugfs.joinpath('result.txt').read_text()
 match=re.search(r'RAYPROFILE seq=(\d+) upload=(\d+) arm=(\d+) execute=(\d+) verify=(\d+) audit=(\d+) total=(\d+) bytes=(\d+)',log)
 assert match,label
 row=dict(zip(['sequence','upload_ns','arm_ns','execute_ns','verify_ns','audit_ns','kernel_ns','audit_bytes'],map(int,match.groups())))
 row.update(label=label,wall_ns=end-start,reply_bytes=len(reply),header=decode(reply));row['header'].pop('frame');row['header'].pop('palette');rows.append(row)
 (a.output/'phases.json').write_text(json.dumps(rows,indent=2)+'\n')
try:
 step('reset',request(op=0,columns=0))
 for i in range(160):step('render80',request(keys=i//20%16))
 for i in range(40):step('render10',request(columns=10,keys=8))
 for i in range(20):
  step('snapshot64',request(op=2,columns=0,pixels=0));step('snapshot4864',request(op=2,columns=0))
 for repeat in range(5):
  for reps in [1,16,64,128]:
   for kind in range(9):step(f'bench{kind}x{reps}',request(op=3,columns=0,pixels=0,kind=kind,reps=reps))
finally:
 print(json.dumps(board.close()))
