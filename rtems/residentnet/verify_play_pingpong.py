"""Doom ping-pong journal replay. Invoked after all legacy pairs/frames/STOP checks."""
import hashlib,json,statistics,struct

def verify_transport(out,frames,epoch,source,compared,controls):
 from verify_release import verify as verify_release
 release_timing=verify_release(out)
 final=json.loads((out/'doom-pingpong-result.json').read_text())
 n=final['frames'];assert (n in (52,100) or (100<=n<=1000 and n%2==0)) and final['stopped_held']==[n-1,n]
 assert final['manifest']['pingpong'] and final['manifest']['double_buffer']
 stats=final['stats'];assert len(stats)==6 and stats[0]==n-16 and stats[1]>0 and stats[2:5]==[n-1,n,2]
 # Full snapshots may run between active DMA intervals; positive overlap is
 # reported separately, never manufactured by weakening the full audit.
 base=None;active=False;released=[];sets={};completions=set();captured=set();stats_seen=False;clocks=[];cycles={}
 for line in (out/'pingpong-journal.jsonl').read_text().splitlines():
  r=json.loads(line);assert r['ns']>0
  if 'errno' in r:
   assert r['op']==2 and r['errno']==11 and 17<=r['g']<=n and r['off']==0
   continue
  q=bytes.fromhex(r['request']);b=bytes.fromhex(r['response']);assert len(q)==len(b)==(73760 if struct.unpack_from("<I",q)[0]==8 else 1056) and q[:32]==b[:32] and not any(q[32:])
  op,e,g,off,*zero=struct.unpack_from('<8I',q);assert e==epoch and not any(zero);v=b[32:]
  if op==1:
   assert base is None and not g and not off;base=struct.unpack_from('<2I',v);assert not any(v[8:])
   assert all(0<x<=0xffffffff-73728 for x in base) and (base[0]+73728<=base[1] or base[1]+73728<=base[0])
  elif op==6:assert base and not active and g==17 and not off and not any(v);active=True
  elif op==7:assert not g and not off and not any(v[4:]);clocks.append(struct.unpack_from('<I',v)[0])
  elif op==5:
   assert not g and not off and not any(v[24:]) and list(struct.unpack_from('<6I',v))==stats;stats_seen=True
  else:
   assert active and 17<=g<=n
   assert all(x in released for x in range(17,g-1)), 'destination reused without prior release'
   if op==2:
    assert not off and not any(v[32:]);m=struct.unpack_from('<8I',v)
    assert m[:5]==(0x31505044,g,(g-1)&1,65536,source+((g-1)&1)*65536) and m[6:]==((~g)&0xffffffff,g)
    assert tuple(m)==struct.unpack_from('<8I',(out/f'pingpong-{g:03}.bin').read_bytes(),73696)
    completions.add(g)
   elif op in (3,8):
    assert g in completions
    assert (op==8 and off==73728) or (op==3 and off%1024==0 and 0<=off<=72704)
    d=sets.setdefault(g,{})
    if op==8:
     assert not d or len(d)==72
     d.clear();d.update({i:v[i:i+1024] for i in range(0,73728,1024)})
    else:
     if off==0 and len(d)==72:d.clear()
     assert off==len(d)*1024
     d[off]=v
    if len(d)==72:
     cycles[g]=cycles.get(g,0)+1
     capture=b''.join(d[o] for o in range(0,73728,1024));assert capture==(out/f'pingpong-{g:03}.bin').read_bytes()
     assert capture[:4096]==b'\xa5'*4096 and capture[69632:73696]==b'\xa5'*4064
     m=struct.unpack_from('<8I',capture,73696)
     assert m[:5]==(0x31505044,g,(g-1)&1,65536,source+((g-1)&1)*65536) and m[6:]==((~g)&0xffffffff,g)
     assert capture[4096:69632]==(out/f'play-0-{g}.bin').read_bytes();captured.add(g)
   elif op==4:assert not off and not any(v) and g in captured and g not in released;released.append(g)
   else:raise AssertionError('unknown ping-pong operation')
 assert all(len(v)==72 for v in sets.values())
 assert cycles=={g:3 if g==18 else 2 if g in (17,n-1,n) else 1 for g in range(17,n+1)}
 assert released==list(range(17,n-1)) and captured==set(range(17,n+1)) and stats_seen
 stall=json.loads((out/'doom-pingpong-stall.json').read_text());assert stall['frames']==[17,18] and 3<=stall['seconds']<10 and stall['unchanged']
 assert [s['card_ms'] for batch in final['clocks'] for s in batch]==clocks and len(clocks)==6
 windows=[(max(s['before']-(s['card_ms']+10)/1000 for s in batch),min(s['after']-s['card_ms']/1000 for s in batch)) for batch in final['clocks']]
 assert all(a<=b for a,b in windows);lo=min(w[0] for w in windows);hi=max(w[1] for w in windows)
 for g,f in enumerate(frames,1):
  assert f['transport']==('host-dma' if g<=16 else 'pingpong')
  if g>16:
   assert f['released']==(g<n-1) and f['marker']==list(struct.unpack_from('<8I',(out/f'pingpong-{g:03}.bin').read_bytes(),73696))
 def fps(a,b):return (b-a)/(frames[b-1]['seconds']-frames[a-1]['seconds'])
 baseline=fps(5,15);steady=fps(21,50)
 latency=[(max(0,f['observed']-hi-(f['marker'][5]+10)/1000),f['observed']-lo-f['marker'][5]/1000) for f in frames[20:50]]
 return dict(release_timing=release_timing,input_events=[v for i,v in controls if i==2],fps_comparison_valid=not final['manifest'].get('runtime_detail',False) and (n>=100 or not any(i==2 for i,v in controls)),frames=n,full_guarded_bytes=n*73728,mailbox_pairs=compared,host_dma_fps=baseline,pingpong_fps=steady,improvement_percent=(steady/baseline-1)*100,baseline_interval=[5,15],pingpong_interval=[21,50],start_to_host_observed_mean_bounds_ms=[statistics.mean(v[i] for v in latency)*1000 for i in (0,1)],ready_to_release_mean_ms=1000*statistics.mean(f['ready_to_release_seconds'] for f in frames[20:50]),stall=stall,held_stop=True,system_dma_lease_checks=stats[5])
