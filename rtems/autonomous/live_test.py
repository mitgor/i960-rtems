#!/usr/bin/env python3
"""Explicit card test: hardware-clock tasks must progress with no host STEP."""
import argparse,json,struct,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board
MAGIC=0x31415452

def step(board,op):
 w=struct.unpack('<16I',board.step(struct.pack('<4I',MAGIC,op,0,0)))
 assert w[0]==MAGIC and w[1]==0,w
 return dict(ticks=w[2],wakes=w[3],iterations=w[4],last_wake_tick=w[6],armed=w[15],mask=w[7],imap=w[8],vector=w[9],saved_vector=w[10],timer_count=w[12],timer_mode=w[13])
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--payload',type=Path,required=True);p.add_argument('--module',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--seconds',type=float,default=3);a=p.parse_args()
 board=Board(a.payload,a.module,a.output,autonomous=True)
 try:
  start=step(board,1);t=time.monotonic();assert start['armed']==1
  # No read/write/poll of the card occurs during this interval.
  time.sleep(a.seconds)
  end=step(board,0);elapsed=time.monotonic()-t
  assert end['armed']==1 and end['ticks']>start['ticks']+10 and end['wakes']>start['wakes']+10
  result=dict(start=start,end=end,host_silent_seconds=a.seconds,elapsed_s=elapsed,observed_hz=(end['ticks']-start['ticks'])/elapsed,host_steps=2)
  (a.output/'acceptance.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
 finally:print(json.dumps(board.close()),flush=True)
if __name__=='__main__':main()
