#!/usr/bin/env python3
"""Run bounded pending-callback MU STOP1 acceptance on the exclusively owned card."""
import argparse,json,secrets,struct,subprocess,sys
from pathlib import Path
from live_test import decode
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board

def decode_stop(data):
 assert len(data)==816,len(data)
 row=decode(data[:736]);d=struct.unpack('<20I',data[736:])
 assert d[0]==0x31505453 and 0<d[1]<=65535 and d[2]==8,d
 assert 32<=d[3]<=64 and d[4] in [int(s['owner'],16) for s in row['slots']],d
 assert d[5:9]==(1,1,1,1),d
 assert d[9]==d[3]==row['ticks'] and d[10:12]==tuple(s['returns'] for s in row['slots']),d
 assert d[12]>0 and d[13]==0x4d554f4b and d[14:]==(0,0,0,0,0,0),d
 row['stop']=dict(zip(('magic','epoch','ready_tick','stop_tick','interrupted_owner',
   'a_live_at_stop','b_live_at_stop','irq_dispatch_depth','irq_nesting',
   'drained_tick','a_returns','b_returns','release_budget','mu_restored','event_status'),d[:15]))
 return row

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['payload','module','output','reader']:p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);rows=[]
 for index,delay in enumerate((120,150,200)):
  before=json.loads(subprocess.check_output([str(a.reader)],text=True))
  board=Board(a.payload,a.module,a.output/f'run-{index}')
  (board.out/'mu-before.json').write_text(json.dumps(before,indent=2)+'\n')
  try:
   epoch=secrets.randbelow(65535)+1
   data=board.step(struct.pack('<3I',0x31505453,epoch,delay))
   (board.out/'stop.bin').write_bytes(data);row=decode_stop(data)
   assert row['stop']['epoch']==epoch
   log=(board.debugfs/'result.txt').read_text();(board.out/'stop-log.txt').write_text(log)
   assert f'callback pending=1 sequence=1 delay_ms={delay} epoch={epoch}' in log
   assert 'STOP1 DRAINED; callback pending=1 sequence=1; sending RELEASE' in log
   assert 'STOP1 callback returned; MU words/masks restored, host OISR acknowledged' in log
   rows.append(row);(board.out/'acceptance.json').write_text(json.dumps(row,indent=2)+'\n')
   print(json.dumps(row),flush=True)
  finally:print(json.dumps(board.close()),flush=True)
  after=json.loads(subprocess.check_output([str(a.reader)],text=True))
  (board.out/'mu-after.json').write_text(json.dumps(after,indent=2)+'\n')
  for sample in after['samples']:
   for n in ('IMR1','OMR1','IIMR','OIMR'):assert sample[n]==before['samples'][0][n],n
   for n in ('IISR','OISR'):assert int(sample[n],16)&2==int(before['samples'][0][n],16)&2,n
 (a.output/'acceptance.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()
