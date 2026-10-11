#!/usr/bin/env python3
"""Critical-section STOP and deliberately omitted STOP/RELEASE hardware acceptance."""
import argparse,json,secrets,struct,subprocess,sys
from pathlib import Path
from live_test import decode
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board

def decode_cases(data):
 assert len(data)==896,len(data)
 d=struct.unpack('<20I',data[736:816]);c=struct.unpack('<20I',data[816:]);mode=c[0]
 assert mode in (1,2,3,4)
 row=decode(data[:736],expected_fault=16384 if mode==4 else 0)
 assert d[0]==0x31505453 and 0<d[1]<=65535 and d[13]==0x4d554f4b
 assert d[9]==row['ticks'] and d[10:12]==tuple(s['returns'] for s in row['slots'])
 assert d[15:]==(0,0,0,0,0)
 assert (d[12]==0)==(mode==4) and d[14]==(6 if mode==3 else 0)
 assert c[11]==d[9] and c[12]==0
 if mode<=2:
  assert c[1]>=16 and c[2]-c[1]==12 and c[3]-c[2]==12
  assert c[4]==c[3]==c[11]
  assert c[5:9]==(2,1,1,0) and c[9]==c[10] and c[9]>5
  assert c[13:16]==(12,12,0) and c[16]>0 and c[17]==mode
  assert c[mode]<=d[2]<d[3]<=c[mode+1] and d[2]==c[mode]+1
  assert d[4]==int(row['slots'][0]['owner'],16) and d[5:7]==(1,1)
  assert d[7:9]==(4-mode,1) and d[9]>d[3]
 else:
  assert d[2]==8 and not any(c[1:11]) and not any(c[13:])
  if mode==3:assert d[3:9]==(0,0,0,0,0,0) and d[9]==128
  else:
   assert 32<=d[3]<=64 and d[3]==d[9]
   assert d[4] in [int(s['owner'],16) for s in row['slots']] and d[5:9]==(1,1,1,1)
 assert not any(c[18:])
 row['case']=mode;row['stop_words']=list(d);row['critical_words']=list(c)
 return row

def check_log(log,mode,epoch):
 assert f'STOPCASE READY case={mode} pending=1 sequence=1 epoch={epoch}' in log
 assert f'STOPCASE DRAINED case={mode} pending=1 sequence=1' in log
 assert ('STOPCASE intentionally omitting STOP' in log)==(mode==3)
 assert ('STOPCASE intentionally omitting RELEASE' in log)==(mode==4)
 assert 'STOP1 callback returned; MU words/masks restored, host OISR acknowledged' in log

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('payload','module','output','reader'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--repeats',type=int,default=3);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);rows=[]
 for repetition in range(a.repeats):
  for mode in (1,2,3,4):
   before=json.loads(subprocess.check_output([str(a.reader)],text=True))
   board=Board(a.payload,a.module,a.output/f'run-{repetition}-{mode}')
   (board.out/'mu-before.json').write_text(json.dumps(before,indent=2)+'\n')
   try:
    epoch=secrets.randbelow(65535)+1
    data=board.step(struct.pack('<3I',0x31505453,epoch,mode))
    (board.out/'cases.bin').write_bytes(data);row=decode_cases(data)
    assert row['case']==mode and row['stop_words'][1]==epoch
    log=(board.debugfs/'result.txt').read_text();(board.out/'stop-log.txt').write_text(log);check_log(log,mode,epoch)
    row['repetition']=repetition;rows.append(row)
    (board.out/'acceptance.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row),flush=True)
   finally:print(json.dumps(board.close()),flush=True)
   after=json.loads(subprocess.check_output([str(a.reader)],text=True));(board.out/'mu-after.json').write_text(json.dumps(after,indent=2)+'\n')
   for sample in after['samples']:
    for n in ('IMR1','OMR1','IIMR','OIMR'):assert sample[n]==before['samples'][0][n]
    for n in ('IISR','OISR'):assert int(sample[n],16)&2==int(before['samples'][0][n],16)&2
 (a.output/'acceptance.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()
