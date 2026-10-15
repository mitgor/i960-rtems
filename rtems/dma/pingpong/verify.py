#!/usr/bin/env python3
"""Replay both transports, every guarded byte, releases, stall and STOP evidence.
Run residentnet/verify.py separately for all full system/RAM audits.
"""
import argparse,hashlib,json,statistics,struct
from pathlib import Path

# Captures contain Linux errno values, independent of the replay host OS.
def verify(out):
 out=Path(out);rows=lambda n:[json.loads(x) for x in (out/n).read_text().splitlines()]
 assert all(r['words'][34]==145 and r['words'][36:38]==[0,0] for r in rows('ram-diagnostics.jsonl'))
 final=json.loads((out/'pingpong-result.json').read_text());n=final['frames'];assert 64<=n<=512 and n%2==0
 assert final['zero_wad_reads'] and not (out/'wad-journal.jsonl').exists()
 assert final['manifest']['pingpong'] and final['manifest']['double_buffer']
 assert final['result'][:5]==[0x454e4750,3,65536,0,0] and n+2<=final['result'][5]<=n+3 and final['result'][6:]==[0,0,0,2,1,210]
 assert final.get('protocol_version',1) in (1,2)
 if final.get('protocol_version')==2:assert len(final['stats'])==6 and final['stats'][5]>0
 assert final['reply'][5]==0x454e4702 and final['stalled_stop'] and final['held_frames']==2 and final['stats'][4]==2
 expected=lambda g:bytes(((i*13)^(i>>8)^(g*37))&255 for i in range(65536))
 def capture(g,pp):
  b=(out/f'{"pingpong" if pp else "frame-dma"}-{g:03}.bin').read_bytes();assert len(b)==73728 and b[:4096]==bytes([165])*4096
  assert b[4096:69632]==expected(g)
  assert b[69632:73696 if pp else 73728]==bytes([165])*(4064 if pp else 4096)
  if pp:
   m=struct.unpack_from('<8I',b,73696);assert m[:4]==(0x31505044,g,(g-1)&1,65536) and m[6:]==((~g)&0xffffffff,g)
   assert 0xc0240000<=m[4]<=0xc0e30000 and not m[4]&3
  return b
 caps={g:capture(g,g>16) for g in range(1,n+3)}
 # Old transport: exact request order, all status words, full bytes, repeated first page.
 old=iter(rows('frame-dma-journal.jsonl'));epoch=None;bus=desc=None;sources={};reports=rows('frame-dma-results.jsonl')
 def call(op,g,off=0):
  nonlocal epoch
  e=next(old);q=bytes.fromhex(e['request']);h=struct.unpack_from('<8I',q)
  assert len(q)==1056 and h[0]==op and 0<h[1]<=65535 and h[2:]==(g,off,0,0,0,0) and q[32:]==bytes(1024) and e['ns']>0
  if epoch is None:epoch=h[1]
  assert h[1]==epoch
  if 'errno' in e:assert op==2 and e['errno']==11;return None
  r=bytes.fromhex(e['response']);assert len(r)==1056 and r[:32]==q[:32];return r[32:]
 for g in range(1,17):
  assert call(1,g,1)==bytes(1024)
  r=call(2,g)
  while r is None:r=call(2,g)
  w=list(struct.unpack_from('<16I',r));assert r[64:]==bytes(960)
  assert w[:3]==[0x314d4446,2,g] and w[5:8]==[0,0,0] and w[8]==w[15] and w[9:12]==[0,0,7] and w[12]<200000 and w[13:15]==[0,1]
  assert 0xc0f4c010<=w[15]<=0xc0f8bfe0 and not w[15]&31 and 4096<w[3]<=0xffffffff-65536
  if bus is None:bus,desc=w[3],w[15]
  assert (bus,desc)==(w[3],w[15]);sources[(g-1)&1]=w[4]
  assert b''.join(call(3,g,i) for i in range(0,73728,1024))==caps[g]
  assert call(3,g,4096)==caps[g][4096:5120] and reports[g-1]['report']==w
 assert next(old,None) is None and len(reports)==16 and sources[1]-sources[0]==65536
 # New transport state, including the deliberately rejected ownership calls.
 enabled=setup=False;nextg=[17,18];read=[set(),set()];releases=[];errors=[];clocks=[];stats=[]
 for e in rows('pingpong-journal.jsonl'):
  assert e['ns']>0
  if 'errno' in e:
   op,g,off=e['op'],e['g'],e['off'];assert off==0
   assert (op==2 and e['errno']==11 and g==nextg[(g-1)&1]) or (op==4 and e['errno']==116 and g in (15,n-1)) or (op==4 and e['errno']==16 and g==19)
   errors.append((op,g,e['errno']));continue
  q=bytes.fromhex(e['request']);r=bytes.fromhex(e['response']);h=struct.unpack_from('<8I',q);op,ep,g,off=h[:4]
  assert len(q)==len(r)==1056 and ep==epoch and h[4:]==(0,0,0,0) and q[32:]==bytes(1024) and r[:32]==q[:32]
  b=r[32:];slot=(g-1)&1
  if op==1:
   assert not setup and not g and not off;setup=True;addresses=list(struct.unpack_from('<2I',b));assert addresses==final['addresses'] and b[8:]==bytes(1016)
   assert all(0<a<0xffffffff-73728 for a in addresses) and abs(addresses[1]-addresses[0])>=73728
  elif op==6:assert setup and not enabled and g==17 and not off and b==bytes(1024);enabled=True
  elif op==7:assert setup and not g and not off and b[4:]==bytes(1020);clocks.append(struct.unpack_from('<I',b)[0])
  elif op==5:assert enabled and not g and not off;size=len(final['stats']);assert size in (5,6) and b[4*size:]==bytes(1024-4*size);stats.append(list(struct.unpack_from('<'+str(size)+'I',b)))
  else:
   assert enabled and g==nextg[slot] and 17<=g<=n+2
   if op==2:assert not off and b[:32]==caps[g][73696:] and b[32:]==bytes(992)
   elif op==3:assert off%1024==0 and 0<=off<=72704 and b==caps[g][off:off+1024];read[slot].add(off)
   else:
    assert op==4 and not off and b==bytes(1024) and read[slot]==set(range(0,73728,1024));releases.append(g);read[slot].clear();nextg[slot]+=2
 assert releases==list(range(17,n+1)) and nextg==[n+1,n+2] and all(len(x)==72 for x in read)
 assert (4,15,116) in errors and (4,19,16) in errors and (4,n-1,116) in errors
 assert len(stats)==3 and stats[-1]==final['stats'] and stats[0][2:4]==[17,18] and stats[1][2:4]==[n+1,n+2] and all(x[1]>0 for x in stats)
 for g in range(17,n+3):assert struct.unpack_from('<I',caps[g],73712)[0]==sources[(g-1)&1]
 stalls=rows('pingpong-stalls.jsonl');assert len(stalls)==2
 for s,g in zip(stalls,(17,n+1)):assert s['first']==g and s['seconds']>=3 and s['unchanged'] and s['stats'][2:4]==[g,g+1]
 # Exact paired mailbox captures; regular host ACKs must stop at transition.
 mail=iter(rows('frame-journal.jsonl'))
 for g in (1,2,3,4,16):
  for off in range(0,65536,1024):
   e=next(mail);q=bytes.fromhex(e['request']);r=bytes.fromhex(e['response']);assert e['op']==11 and e['ns']>0 and len(q)==len(r)==1056
   assert struct.unpack_from('<10I',q)==(11,epoch,8,0,0,0,0,0,g,off) and q[40:]==bytes(1016)
   rh=struct.unpack_from('<8I',r);assert rh[:4]==(11,epoch,1024,1) and not rh[4]&1 and rh[5:]==(0,0,0) and r[32:]==caps[g][4096+off:5120+off]
 assert next(mail,None) is None
 acks=[]
 for e in rows('upload-journal.jsonl'):
  if e['op']!=10:continue
  q=bytes.fromhex(e['request']);r=bytes.fromhex(e['response']);i,v=struct.unpack_from('<2I',q,32)
  if i==1:assert struct.unpack_from('<I',r,32)[0]==0;acks.append(v)
 assert acks==list(range(1,17))
 owned=rows('owned-journal.jsonl');stops=[e for e in owned if e['op']==6];assert len(stops)==1
 q=bytes.fromhex(stops[0]['request']);r=bytes.fromhex(stops[0]['response']);assert struct.unpack_from('<I',q,32)[0]==0x3252444f and r[32:]==q[32:]
 frames=rows('pingpong-frames.jsonl');assert [f['frame'] for f in frames]==list(range(1,n+1)) and all(f['service_seconds']>0 for f in frames)
 for f in frames[16:]:
  g=f['frame'];assert f['marker']==list(struct.unpack_from('<8I',caps[g],73696)) and f['sha256']==hashlib.sha256(caps[g]).hexdigest()
 def fps(lo,hi):return (hi-lo)/(frames[hi-1]['seconds']-frames[lo-1]['seconds'])
 baseline=fps(5,15);ring=fps(21,n)
 calibration=rows('pingpong-clocks.jsonl');assert len(calibration)==2 and [s['card_ms'] for a in calibration for s in a]==clocks
 # Tick is quantized down by 10 ms. Conservative offset interval per exchange.
 windows=[]
 for samples in calibration:
  low=max(s['before']-(s['card_ms']+10)/1000 for s in samples);high=min(s['after']-s['card_ms']/1000 for s in samples);assert low<=high;windows.append([low,high])
 # Include both calibrations: clock drift/measurement uncertainty widens bounds.
 low=min(w[0] for w in windows);high=max(w[1] for w in windows)
 lat=[(f['detected_monotonic']-f['marker'][5]/1000-high-.010,f['detected_monotonic']-f['marker'][5]/1000-low) for f in frames[20:]]
 costs={}
 for name in ('frame-dma-journal.jsonl','pingpong-journal.jsonl'):
  groups={}
  for e in rows(name):
   op=struct.unpack_from('<I',bytes.fromhex(e['request']))[0] if 'request' in e else e['op']
   groups.setdefault(str(op),[]).append(e['ns']/1e6)
  costs[name]={op:dict(calls=len(v),mean_ms=statistics.mean(v),max_ms=max(v)) for op,v in groups.items()}
 return dict(system_dma_lease_checks=final['stats'][5] if len(final['stats'])==6 else None,ioctl_costs=costs,frames=n,guarded_frames=n+2,paired_mailbox_frames=5,full_guarded_bytes=(n+2)*73728,exact_pattern_bytes=(n+2)*65536,stalls=stalls,owned_stop=True,host_started_fps=baseline,card_started_fps=ring,improvement_percent=(ring/baseline-1)*100,baseline_interval_frames=[5,15],ring_interval_frames=[21,n],card_started_stall_inclusive_fps=fps(16,n),ready_to_copy_release_mean_ms=1000*statistics.mean(f['ready_to_copy_release_seconds'] for f in frames[20:]),start_to_validated_capture_release_mean_bounds_ms=[1000*statistics.mean(p[i]+f['ready_to_copy_release_seconds'] for p,f in zip(lat,frames[20:])) for i in (0,1)],start_to_host_observed_mean_bounds_ms=[1000*statistics.mean(p[i] for p in lat) for i in (0,1)],clock_offset_windows=windows,ioctl_counts=dict(host_started=len(rows('frame-dma-journal.jsonl')),card_started=len(rows('pingpong-journal.jsonl'))),sources=sources)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('capture',type=Path);a=p.parse_args();print(json.dumps(verify(a.capture),indent=2))
