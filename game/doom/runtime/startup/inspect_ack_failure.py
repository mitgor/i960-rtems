#!/usr/bin/env python3
"""Diagnose the captured ACK-index truncation; never accept the incomplete batch."""
import argparse,gzip,hashlib,json,struct,sys,zlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'rtems/residentnet'))
from verify import snapshot_gate
from large_contract import validate_large,validate_large_stacks
from run import ROM_SHA
import wire
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--wad',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();c=a.root/'live';data=a.wad.read_bytes()
assert hashlib.sha256(data).hexdigest()=='7323bcc168c5a45ff10749b339960e98314740a734c30d4b9f3337001f9e703d'
trace=list(struct.iter_unpack('<2I',(a.root/'admission/startup-requests.bin').read_bytes()));records={};parts={};last=0;epochs=set();total=0;fragments=0
for line in (c/'engine-wad-journal.jsonl').open():
 e=json.loads(line);assert 'errno' not in e;q=bytes.fromhex(e['request']);s=bytes.fromhex(e['response']);assert len(q)==len(s)==1056
 op,epoch,n,*zero=struct.unpack_from('<8I',q);h=struct.unpack_from('<8I',s);assert not any(zero) and epoch and h[:2]==(op,epoch) and h[3:]==(1,0,0,0,0);epochs.add(epoch)
 if op==3:
  assert n==0 and h[2]==32;w=struct.unpack_from('<8I',s,32)
  if w[0]!=0x31424157:assert w[0]==0x31444157 and w[2]==0;continue
  if w[2]!=1:continue
  seq=w[1];pair=w[4:6];assert w[3]==1 and w[6]==len(data) and 0<pair[1]<=4096 and pair[0]+pair[1]<=len(data)
  assert records.get(seq,pair)==pair;records[seq]=pair;last=seq
 else:
  assert op==4 and 32<=n<=544 and n%4==0 and h[2]==n and s[32:32+n]==q[32:32+n]
  w=struct.unpack_from('<8I',q,32);seq=w[1];assert seq==last and seq in records;off,want=records[seq];done=parts.get(seq,0);size=min(512,want-done)
  assert size>0 and w[:6]==(0x31424157,seq,1,off+done,size,0) and w[7]==want
  block=data[off+done:off+done+size];assert w[6]==zlib.crc32(block) and q[64:64+size]==block and n==32+((size+3)&~3) and not any(q[64+size:32+n])
  parts[seq]=done+size;total+=size;fragments+=1
assert len(epochs)==1 and list(records)==list(range(1,len(records)+1))
assert len(records)==9420 and parts[4749]==1536 and records[4749]==trace[1]
assert all(parts[k]==n for k,(off,n) in records.items() if k!=4749)
assert list(records.values())==trace+trace[:2]+trace[:4671]
observed=list(records.values());prefix=next((i for i,(x,y) in enumerate(zip(trace,observed)) if x!=y),min(len(trace),len(observed)))
from checkpoint_replay import check
cp=check(c,a.root/'admission');assert cp['uncertain_errno']==116 and cp['pending_ack']==(272,6)
assert cp['acknowledged_records']==26 and cp['comparisons'][0]['matching_prefix']==199 and cp['comparisons'][2]['matching_prefix']==68
assert 'Stale file handle' in (c/'error.txt').read_text() and not (c/'engine-results.json').exists()
assert 'SESSION FAILED: retained DMA/module; reboot required' in (c/'retained-close/result.txt').read_text()
snaps=json.loads((c/'snapshots.json').read_text());ram=[json.loads(l) for l in (c/'ram-diagnostics.jsonl').read_text().splitlines()];assert len(snaps) in (len(ram),len(ram)+1)
identity=json.loads((c/'request.json').read_text());code=(a.root/'residentnet/kernel.bin').read_bytes()
assert hashlib.sha256(code).hexdigest()==identity['payload_sha256'] and hashlib.sha256(wire.prepare(code)).hexdigest()==identity['image_sha256']
assert any(hashlib.sha256(p.read_bytes()).hexdigest()==identity['module_sha256'] for p in a.root.glob('residentnet-module*/dac960auto.ko'))
original=(c/'open/stage-before-a5.bin').read_bytes();assert hashlib.sha256(original).hexdigest()==ROM_SHA and original==(c/'open/stage-before-5a.bin').read_bytes()
raw=gzip.decompress((c/'trace.bin.gz').read_bytes());ns,n=struct.unpack_from('<QI',raw);assert ns>0 and n==16
request=raw[12:28];n=struct.unpack_from('<I',raw,28)[0];assert n==640 and len(raw)==32+n
arm=struct.unpack('<4I',request);assert arm[:2]==(0x31415452,1) and arm[3]&255==2 and epochs=={arm[2]}
audit=gzip.decompress((c/'audit-000001.bin.gz').read_bytes());before=wire.prepare(code)[:wire.bio.OFFSET]+wire.block(request,1)+original[wire.bio.IMAGE_SIZE:]
assert wire.response(before,audit+original[len(audit):])==(0,raw[32:]) and audit[0x60000:0x6fff0]==before[0x60000:0x6fff0]
groups=[[],[],[]];page=None;words=None;events=json.loads((c/'controls.json').read_text());assert events==[json.loads(l) for l in (c/'control-journal.jsonl').read_text().splitlines()]
for e in events:
 if 'words' not in e:continue
 w=e['words'];assert w[3]==1 and w[6:]==[0,0] and not w[4]&1
 tag={4:0x8b000000,5:0x92000000|(e['arg']<<16),7:0x99000000 if e['arg']==2 else 0x97000000 if e['arg']==1 else 0x95000000}[e['op']];assert w[5]==tag|arm[2]
 if e['op']==7:
  if words is not None:assert len(words)==64;groups[page].append(words)
  page=e['arg'];assert page in (0,1,2);words=[]
 elif e['op']==5:assert e['arg']==len(words);words.append(w[2])
partial_page=None
if len(words)==64:groups[page].append(words)
else:
 assert page in (0,1,2) and 0<len(words)<64
 if page==2:assert len(snaps)==len(ram)+1
 else:assert len(snaps)==len(ram)
 partial_page=dict(page=page,words=words)
assert groups[0][:-1]==[s['words'] for s in snaps] and groups[2]==[r['words'] for r in ram]
assert groups[0][-1]==json.loads((c/'failure-snapshot.json').read_text())
snapshot_gate(groups[0][-1],arm[2],True,True,True,True)
assert groups[1]==[d['words'] for d in json.loads((c/'heap-diagnostics.json').read_text())]
for s in snaps:
 w=s['words'];assert w[2:5]==[1,0,0];snapshot_gate(w,arm[2],True,True,True,True);validate_large_stacks(w)
for r in ram:validate_large(r['words'],12,False)
for d in groups[1]:assert d[0]==0x314c5348 and d[54]==0 and d[55]==d[63]==1
for x,y in zip(snaps,snaps[1:]):assert y['seconds']>x['seconds'] and all(y['words'][i]>=x['words'][i] for i in (5,6,7,50,51,60,61,62))
out=dict(accepted=False,diagnostic_only=True,actual_requests=len(observed),expected_completed_normal_requests=len(trace),first_normal_request_trace_matches=True,repeat_prefix_requests=4671,stop_partial_sequence=4749,stop_partial_bytes=1536,verified_payload_bytes=total,fragments=fragments,all_payloads_match_wad=True,last_tick=snaps[-1]['words'][5],last_capture_seconds=snaps[-1]['seconds'],full_snapshot_pairs=len(ram),complete_snapshots=len(snaps),additional_unpaired_failure_snapshot=True,last_partial_page=partial_page,captured_fault_markers_zero=True,initial_image_and_paired_audit_checked=True,full_frozen_pages_reconstructed=True,checkpoint_replay=cp,final_repeat_outcome_known=False,completed_network_rounds=1+max(r['round'] for r in json.loads((c/'network-progress.json').read_text())))
a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
