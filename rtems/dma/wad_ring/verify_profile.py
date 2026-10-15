#!/usr/bin/env python3
"""Replay read-only profile reports and cache telemetry; requires normal full verifiers too."""
import argparse,json,struct
from pathlib import Path
NAMES=('read_total','frame_barrier','allocation_and_loans','staging_init','release_and_returns','guards','dma_start_to_completion','transfer_total','response_wait','service_yield','staging_copy','benchmark_transfer','benchmark_hardware','benchmark_guards','empty_bracket','benchmark_verify','response_transfer','allocation_only','free_only')
def verify(path):
 p=Path(path);words=json.loads((p/'wad-profile.json').read_text())['words']
 assert len(words)==65 and words[0]==0x31525057 and words[1] in (2,3,4) and words[2:6]==[4166700,64,64,32768]
 if words[1]==2:assert words[6:8]==[0,0]
 else:assert 0<words[6]<=100 and words[7]>0, 'peer service gap exceeds one-second acceptance bound'
 requests=[];replies={}
 for line in (p/'upload-journal.jsonl').read_text().splitlines():
  row=json.loads(line);q=bytes.fromhex(row['request'])
  if row['op']==1:
   h=struct.unpack_from('<8I',q,32)
   if h[2]==21 and h[3]>=8:
    assert h[4:]==(0,0,0,0) and 8<=h[3]<73;requests.append((h[1],h[3]-8))
  if row['op']==2:
   b=bytes.fromhex(row['response']);h=struct.unpack_from('<16I',b,32)
   if h[0]==0x31525055 and h[3]==0:replies[h[1]]=h
 assert len(requests)==65 and [i for s,i in requests]==list(range(65))
 assert [replies[s][5] for s,i in requests]==words and all(replies[s][2]==0 for s,i in requests)
 metrics={}
 for i,name in enumerate(NAMES):
  count,lo,hi=words[8+3*i:11+3*i];assert count and 0<=lo<=0xffffffff and 0<=hi<=0xffffffff
  metrics[name]=dict(count=count,seconds=((hi<<32)|lo)/words[2])
 assert metrics['benchmark_transfer']['count']==metrics['benchmark_hardware']['count']==metrics['benchmark_verify']['count']==64
 assert metrics['benchmark_guards']['count']==128
 assert metrics['guards']['count']==2*metrics['transfer_total']['count']
 assert metrics['transfer_total']['count']==metrics['dma_start_to_completion']['count']
 assert metrics['response_transfer']['count']>=2*metrics['response_wait']['count']
 s=lambda n:metrics[n]['seconds']
 assert s('benchmark_transfer')>s('benchmark_hardware') and s('read_total')>s('transfer_total') and s('response_wait')>=s('response_transfer')
 cache=[]
 for g in range(1,101):
  b=(p/f'play-0-{g}.bin').read_bytes();w=struct.unpack_from('<16I',b,64960)
  assert w[:2]==(0x31435057,1) and w[-1]==10
  assert min(w[6:9])>0 and w[10]>0 and w[11]>0 and w[12]>0
  assert w[6]==w[7]==w[8] and all(t%10==0 for t in w[2:6])
  if cache:assert all(x>=y for x,y in zip(w[2:15],cache[-1][2:15]))
  cache.append(w)
 rows=[json.loads(x) for x in (p/'wad-ring-results.jsonl').read_text().splitlines()]
 assert cache[-1][6]==metrics['read_total']['count']
 assert len(rows)==metrics['response_wait']['count']==metrics['staging_copy']['count']
 assert sum(r['wanted'] for r in rows)==cache[-1][10]
 names=('runtime_read','fill_cache','miss_copy_to_doom','hit_copy_to_doom')
 def decode(w):return dict(seconds={n:w[2+i]/1000 for i,n in enumerate(names)},calls=dict(zip(names,w[6:10])),wire_bytes=w[10],copied_bytes=w[11],logical_reads=w[12],cache_hits=w[13],cache_line_misses=w[14])
 host=json.loads((p/'wad-ring-service.json').read_text())
 return dict(peer_policy={2:"equal-timeslice",3:"all-service-passes",4:"owned-execution-only"}[words[1]],peer_yield=words[1]>=3,peer_max_gap_ms=words[6]*10 if words[1]>=3 else None,peer_completed_passes=words[7] if words[1]>=3 else None,timer_hz_nominal=words[2],timer_is_elapsed_not_cpu=True,metrics=metrics,benchmark_bytes=64*32768,benchmark_hardware_MBps=(64*32768/1e6)/s('benchmark_hardware'),benchmark_checked_MBps=(64*32768/1e6)/s('benchmark_transfer'),response_wait_excluding_response_dma_seconds=s('response_wait')-s('response_transfer'),first_frame_cache=decode(cache[0]),final_cache=decode(cache[-1]),warm_restart_cache_ms=[cache[67][i]-cache[65][i] for i in range(2,6)],host=host)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('capture');a=p.parse_args();print(json.dumps(verify(a.capture),indent=2))
