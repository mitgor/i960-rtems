#!/usr/bin/env python3
"""Explicit, one-shot MU echo on an exclusively owned idle card; not a takeover."""
import argparse,fcntl,json,struct,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board
p=argparse.ArgumentParser(description=__doc__)
for name in ['payload','module','output','reader']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args()
def snapshot():return json.loads(subprocess.check_output([str(a.reader)],text=True))
before=snapshot();board=Board(a.payload,a.module,a.output,autonomous=True)
(a.output/'mu-before.json').write_text(json.dumps(before,indent=2)+'\n')
try:
 reply=struct.unpack('<16I',board.step(struct.pack('<4I',0x31415452,1,0,0)))
 assert reply[0]==0x31415452 and reply[1]==0 and reply[15]==1,reply
 token=0xc71e9601;words=bytearray(struct.pack('<8I',token,0,0,0,0,0,0,0))
 start=time.monotonic_ns()
 try:fcntl.ioctl(board.fd,0xc0204d01,words,True)
 finally:
  (a.output/'mu-ioctl.bin').write_bytes(words)
  (a.output/'mu-ioctl-log.txt').write_text(Path('/sys/kernel/debug/dac960auto/result.txt').read_text())
 elapsed=time.monotonic_ns()-start;w=struct.unpack('<8I',words)
 assert w[1]==token^0x5a5a5a5a and w[2]==w[3]==1,w
 result=dict(passed=True,request=hex(token),response=hex(w[1]),firmware_sequence_before=w[2],firmware_sequence_after=w[3],latency_ms=elapsed/1e6,host_steps=board.sequence,meaning='single MU word echoed by timer ISR without another firmware transaction; not independent STOP')
 (a.output/'acceptance.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
finally:
 result=board.close();print(json.dumps(result),flush=True)
 (a.output/'restoration.json').write_text(json.dumps(result,indent=2)+'\n')
 after=snapshot();(a.output/'mu-after.json').write_text(json.dumps(after,indent=2)+'\n')
 for name in ['IMR1','OMR1','IIMR','OIMR']:
  assert all(row[name]==before['samples'][0][name] for row in after['samples']),name
 for name in ['IISR','OISR']:
  assert all(int(row[name],16)&2==int(before['samples'][0][name],16)&2 for row in after['samples']),name
 print('MU values/masks/message-1 pending bits restored',flush=True)
