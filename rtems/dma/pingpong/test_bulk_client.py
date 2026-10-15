#!/usr/bin/env python3
"""Exercise the actual bulk client ABI and its independent capture checks."""
import json,struct,sys,tempfile,threading
from pathlib import Path
from unittest.mock import patch
r=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(r/'rtems/residentnet'),str(r/'rtems/dma/stress'),str(Path(__file__).resolve().parent)]
from pingpong_client import PingPong
from stress_client import pattern
raw=b'\xa5'*4096+pattern(17)+b'\xa5'*4064+struct.pack('<8I',0x31505044,17,0,65536,0xc0800000,123,0xffffffee,17)
calls=[]
def ioctl(fd,cmd,b,mutate):
 assert fd==9 and cmd==0xc4204d0a and mutate and len(b)==73760
 assert struct.unpack_from('<8I',b)==(8,42,17,73728,0,0,0,0) and not any(b[32:])
 calls.append(cmd);b[32:]=raw
with tempfile.TemporaryDirectory() as d:
 p=PingPong(9,42,d,threading.RLock())
 with patch('fcntl.ioctl',ioctl):got,marker=p.capture(17)
 assert got==raw and len(calls)==1
 rows=[json.loads(x) for x in (Path(d)/'pingpong-journal.jsonl').read_text().splitlines()]
 assert len(rows)==1 and bytes.fromhex(rows[0]['response'])[32:]==raw
 assert (Path(d)/'pingpong-017.bin').read_bytes()==raw
print('PASS one bulk ioctl, exact bounded ABI, complete journal and guarded capture')
