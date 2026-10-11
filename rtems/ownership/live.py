#!/usr/bin/env python3
"""Persistent ownership, owner-only handoff, restart generations and quarantine."""
import argparse,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board

def decode(data):
 assert len(data)==256
 w=list(struct.unpack('<64I',data))
 assert w[0:2]==[0x314e574f,1] and w[6]>0 and 0<=w[7]<=4
 assert w[17]==w[2] and w[34]==w[6] and w[35:38]==[0,0,0] and w[40]&0x1f0000==0x1f0000
 assert w[45:48]==[5,0,0] and not any(w[49:]) and len(set(w[18:21]))==3
 assert len(set(w[42:45]))==3 and all(w[18:21]) and all(w[42:45])
 assert w[29]>=w[30] and w[29]-w[30]<=1 and w[28]==0
 if w[7] in (1,2,4):assert w[21]==w[18] and w[22]==w[27]==1
 else:assert w[21]==w[22]==w[27]==0 and w[8]==w[9] and w[10]==0
 if w[29]!=w[30]:assert w[24]&0x400 and w[26]==2
 if w[7]==4:assert w[48]&3==3 and w[38] and w[39]
 if w[5]:assert w[3:6]==[11,0,1] and w[10]==0 and w[48]==7 and all(x&2 for x in w[23:26])
 return w

def run(board,cycles):
 rows=[];epoch=1;last=None;identity=None
 def call(op,value=0,e=None,expected=0):
  nonlocal epoch,last,identity
  req=struct.pack('<4I',0x314e574f,op,epoch if e is None else e,value)
  raw=board.step(req);w=decode(raw);assert w[3]==op and w[4]==expected,(op,w)
  if identity is None:identity=w[18:21]+w[41:46]
  assert identity==w[18:21]+w[41:46],'task/stack/ledger identity changed'
  rows.append(dict(request=req.hex(),report=raw.hex()));epoch=w[6];last=w;return w
 call(0)
 for i in range(cycles):
  committed=last[8];old=epoch
  call(1,0xb0000000+i);call(2,0xa0000000+i);call(7,expected=23)
  w=call(5);ticket=w[11];call(3);call(4,expected=5)
  call(5,expected=2);call(6,ticket+1,expected=1);call(6,ticket,e=old-1,expected=1)
  call(8,expected=3);call(10);call(6,ticket);call(6,ticket,expected=1)
  w=call(4);assert w[31]==committed and w[8]==0xa0000000+i and w[23]==2 and w[26]==3 and w[29]==w[30]==i+1
  call(3,expected=3);call(8);call(1,99,e=old,expected=1)
 # Normal commit and clean restart are also exercised without a waiter.
 call(1,0x33445566);w=call(12);assert w[8]==0x33445566 and w[16]==1;call(8)
 call(1,0xdeadbeef);call(2,0xfeedbeef);w=call(5);ticket=w[11];call(3)
 w=call(9);frozen=w[38:40];held=w[21:23];queued=w[29:31]
 call(4,expected=3);call(8,expected=3);call(7,expected=23);call(11,expected=2)
 for i in range(8):
  w=call(10);assert w[38:40]==frozen and w[21:23]==held and w[29:31]==queued
  call(0)
 call(6,ticket);w=call(11);assert w[5]==1
 (board.out/'final-step.txt').write_text((board.debugfs/'result.txt').read_text())
 (board.out/'ownership.json').write_text(json.dumps(rows,indent=2)+'\n')
 return dict(callbacks=len(rows),epochs=epoch,aborts=w[15],commits=w[16],waiter_handoffs=w[30],other_steps=w[32],quarantine_hashes=frozen,finalized=bool(w[5]))

def main():
 p=argparse.ArgumentParser()
 for n in ('payload','module','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--cycles',type=int,default=20);p.add_argument('--runs',type=int,default=3);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);rows=[]
 for i in range(a.runs):
  b=Board(a.payload,a.module,a.output/f'run-{i}')
  try:row=run(b,a.cycles);rows.append(row);print(json.dumps(row),flush=True)
  finally:print(json.dumps(b.close()),flush=True)
 (a.output/'acceptance.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()
