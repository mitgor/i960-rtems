#!/usr/bin/env python3
"""Explicit framed MU acceptance on the exclusively owned patched card."""
import argparse
import fcntl
import json
import secrets
import struct
import subprocess
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board
from protocol import request, response
p=argparse.ArgumentParser(description=__doc__)
for name in ['payload','module','output','reader']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args()
def snapshot():return json.loads(subprocess.check_output([str(a.reader)],text=True))
before=snapshot();epoch=secrets.randbits(32) or 1
board=Board(a.payload,a.module,a.output,autonomous=True)
(a.output/'mu-before.json').write_text(json.dumps(before,indent=2)+'\n')
records=[]
def exchange(label,frame,seq,halt=False):
    words=bytearray(frame+bytes(80));struct.pack_into('<I',words,33*4,int(halt))
    start=time.monotonic_ns()
    try:fcntl.ioctl(board.fd,0xc0904d02,words,True)
    finally:
        (a.output/(label+'.bin')).write_bytes(words)
        (a.output/'mu-log.txt').write_text((board.debugfs/'result.txt').read_text())
    w=struct.unpack('<36I',words)
    assert w[34]==w[35]==1,w[34:]
    parsed={'halt_ack':hex(w[16])} if halt else response(words[64:128],epoch,seq)
    records.append(dict(label=label,latency_ms=(time.monotonic_ns()-start)/1e6,
                        generation=w[32],firmware_sequence=list(w[34:]),response=parsed))
    (a.output/'exchanges.json').write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps(records[-1]),flush=True)
    return parsed
try:
    arm=struct.unpack('<16I',board.step(struct.pack('<4I',0x31415452,1,epoch,0)))
    assert arm[1]==0 and arm[15]==1,arm
    s=exchange('status',request(epoch,1),1);assert s['status']==0 and not s['stopped']
    ping=request(epoch,2,1,0x960cafe)
    r=exchange('ping',ping,2);assert r['status']==0 and r['value']==0x960cafe
    assert exchange('ping-retry',ping,2)==r
    assert exchange('wrong-epoch',request(epoch^1 or 2,3,2),3)['status']==2
    bad=bytearray(request(epoch,3,2));bad[24]^=1
    assert exchange('bad-checksum',bad,3)['status']==1
    stop=request(epoch,3,2)
    stopped=exchange('stop',stop,3);assert stopped['status']==0 and stopped['stopped']
    assert stopped['value']>s['value'] # RTEMS progressed before STOP
    assert exchange('stop-retry',stop,3)==stopped
    time.sleep(0.2)
    quiet=exchange('stopped-status',request(epoch,4),4)
    assert quiet['stopped'] and quiet['status']==0
    assert quiet['value']==stopped['value'] and quiet['heartbeat']==stopped['heartbeat']
    halted=exchange('halt',bytes(64),0,True);assert halted['halt_ack']=='0x2f000000'
    (a.output/'control-acceptance.json').write_text(json.dumps(dict(epoch=epoch,
        passed=True,host_steps=board.sequence,rtos_ticks_at_stop=stopped['value'],
        independent_stop=True,independent_timer_halt=True,
        limitation='bounded task execution; firmware cleanup still required; not runaway-task preemption'),indent=2)+'\n')
finally:
    try:
        closed=board.close()
        (a.output/'restoration.json').write_text(json.dumps(closed,indent=2)+'\n')
    finally:
        after=snapshot();(a.output/'mu-after.json').write_text(json.dumps(after,indent=2)+'\n')
    for row in after['samples']:
        for n in ['IMR1','OMR1','IIMR','OIMR']:assert row[n]==before['samples'][0][n],n
        for n in ['IISR','OISR']:assert int(row[n],16)&2==int(before['samples'][0][n],16)&2,n
    print('Full RAM, timer and MU restoration verified; module unloaded',flush=True)
