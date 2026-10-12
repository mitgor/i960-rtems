import argparse,json,struct,statistics
from pathlib import Path
a=argparse.ArgumentParser();a.add_argument('capture',type=Path);a.add_argument('--output',type=Path,required=True);args=a.parse_args();p=args.capture;r=json.loads((p/'batch-results.json').read_text());normal=[x for x in r['runs'] if x['mode']=='normal'];means={str(n):statistics.mean(x['seconds'] for x in normal if x['limit']==n) for n in [512,4096]}
rows=[json.loads(l) for l in (p/'batch-wad-journal.jsonl').read_text().splitlines()];cost={}
for op in [3,4]:
 ns=[e['ns'] for e in rows if e['op']==op]
 cost[str(op)]=dict(count=len(ns),total_ms=sum(ns)/1e6,mean_ms=statistics.mean(ns)/1e6)
runs=[];pending=None
for e in map(json.loads,(p/'upload-journal.jsonl').read_text().splitlines()):
 if 'errno' in e:continue
 q=bytes.fromhex(e['request']);op=struct.unpack_from('<I',q)[0]
 if op==1:
  command=struct.unpack_from('<I',q,40)[0];seq=struct.unpack_from('<I',q,36)[0];pending=[command,seq,e['ns']]
 elif pending:
  pending[2]+=e['ns'];w=struct.unpack_from('<16I',bytes.fromhex(e['response']),32)
  if w[1]==pending[1] and not w[3]:
   if pending[0] in (20,21,22):runs.append(dict(command=pending[0],sequence=pending[1],ioctl_ms=pending[2]/1e6,result=w[5],status=w[2]))
   pending=None
out=dict(normal_runs=normal,mean_seconds=means,ratio=means['512']/means['4096'],reduction_percent=100*(1-means['4096']/means['512']),logical_requests_per_normal_run={'512':24,'4096':7},normal_fragments_per_run=24,batch_wad_ioctls=cost,commands=runs,notes=['Timings include eight report queries per run; two observations per limit, not a statistical benchmark.','Both limits use WAB1; this is not a direct legacy WAD1 comparison.','Protocol bytes/fragments are not reduced; metadata request/poll handshakes are amortized.','No on-card Doom initialization, first frame or FPS measurement.'])
args.output.write_text(json.dumps(out,indent=2)+'\n');print(means,out['ratio'],cost)
