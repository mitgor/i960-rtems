#!/usr/bin/env python3
"""Reboot-only resident IPv4/IPv6 test; never sends a second firmware callback."""
import threading
from io_gate import IOGate
import argparse,concurrent.futures,errno,fcntl,gzip,json,os,secrets,select,socket,struct,sys,time,traceback,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'transport'))
from run import Board,capture
from relay import Gateway,CARD,CARD6
import wire
from pump import send_pending
from burst import burst
from packet_log import append_packet,finish_packets
from large_contract import validate_large_stacks,validate_large

def traffic_limits(flags,owned):
 if '-DI960_DOOM_STARTUP' in flags:
  assert owned==12 and '-DI960_DOOM_ENGINE' in flags and '-DI960_WAD_BATCH' in flags
  return 540000,90,60
 return (360000 if owned else 180000),60,60

def clients(rounds=1,parallel=False,interval=0,out=None):
 results=[];start=time.monotonic()
 for iteration in range(rounds):
  delay=start+iteration*interval-time.monotonic()
  if delay>0:time.sleep(delay)
  if parallel:
   with concurrent.futures.ThreadPoolExecutor(max_workers=2) as workers:
    jobs=[workers.submit(client_round,[(family,address)]) for family,address in [(socket.AF_INET,CARD),(socket.AF_INET6,CARD6)]]
    batch=[row for job in jobs for row in job.result()]
  else:batch=client_round()
  for row in batch:row["round"]=iteration;row["completed_seconds"]=time.monotonic()-start
  results.extend(batch)
  if out is not None:(out/'network-progress.json').write_text(json.dumps(results,indent=2)+'\n')
 return results

def client_round(families=None):
 results=[]
 for family,address in (families or [(socket.AF_INET,CARD),(socket.AF_INET6,CARD6)]):
  for n in [1,31,500,1400,1472 if family==socket.AF_INET else 1452]:
   data=bytes((i*7+n)%251 for i in range(n))
   with socket.socket(family,socket.SOCK_DGRAM) as s:
    s.settimeout(8);s.sendto(data,(address,9601));reply,peer=s.recvfrom(4096);assert reply==data and peer[0]==address
   results.append(dict(family=family,protocol='udp',bytes=n,sha256=hashlib.sha256(data).hexdigest()))
  data=bytes(i%251 for i in range(4096))
  with socket.socket(family,socket.SOCK_STREAM) as s:
   s.settimeout(10);s.connect((address,9600));s.sendall(data);reply=b''
   while len(reply)<len(data):
    part=s.recv(4096);assert part;reply+=part
   assert reply==data
  results.append(dict(family=family,protocol='tcp',bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
  with socket.socket(family,socket.SOCK_STREAM) as s:
   s.settimeout(10);s.connect((address,80));s.sendall(b'GET / HTTP/1.0\r\nHost: i960\r\n\r\n');reply=b''
   while True:
    part=s.recv(4096)
    if not part:break
    reply+=part
   assert reply.startswith(b'HTTP/1.0 200 OK') and b'RTEMS resident IPv4/IPv6' in reply
  results.append(dict(family=family,protocol='http',response=reply.decode()))
 return results

def main():
 p=argparse.ArgumentParser();p.add_argument('--bdf',required=True)
 for n in ['payload','module','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--dma-proof',action='store_true')
 p.add_argument('--dma-stop',action='store_true')
 p.add_argument('--dma-deadline-job',action='store_true')
 p.add_argument('--play-dma-test',action='store_true')
 p.add_argument('--play-pipeline',action='store_true')
 p.add_argument('--play-pipeline-test',action='store_true')
 p.add_argument('--play-frame-limit',type=int,default=0)
 p.add_argument('--release-schedule',choices=('baseline','priority','abba','baab'),default=None)
 p.add_argument('--play-no-crc',action='store_true');p.add_argument('--wad-dma',action='store_true');p.add_argument('--wad-ring',action='store_true');p.add_argument('--wad-load-test',action='store_true')
 p.add_argument('--frame-dma-stress',type=int,default=0);p.add_argument('--pingpong',action='store_true')
 p.add_argument('--play-bulk',action='store_true')
 p.add_argument('--play-bulk-test',action='store_true')
 p.add_argument('--play-port',type=int,default=0)
 p.add_argument('--play-accept-frames',type=int,default=0)
 p.add_argument('--audit-interval',type=float,default=3)
 p.add_argument('--resident-upload',action='store_true')
 p.add_argument('--doom-heap',action='store_true')
 p.add_argument('--doom-shared',action='store_true')
 p.add_argument('--doom-runtime',action='store_true')
 p.add_argument('--wad',type=Path)
 p.add_argument('--upload-concurrent',action='store_true')
 p.add_argument('--owned-mib',type=int,choices=(0,1,4,10,12),default=0)
 p.add_argument('--heap-shared',action='store_true')
 p.add_argument('--queue-reclaim',action='store_true')
 p.add_argument('--general-heap',action='store_true')
 p.add_argument('--extra-ram',action='store_true')
 p.add_argument('--fault-owner',action='store_true')
 p.add_argument('--secondary-reset',action='store_true')
 p.add_argument('--burst',action='store_true');p.add_argument('--parallel',action='store_true')
 p.add_argument('--ticks',type=int,default=6000);p.add_argument('--rounds',type=int,default=1)
 p.add_argument('--round-interval',type=float,default=0)
 p.add_argument('--deadline',action='store_true');p.add_argument('--drop-data',action='store_true');a=p.parse_args()
 a.release_schedule=a.release_schedule or ("priority" if a.pingpong and a.play_pipeline_test else "baseline")
 assert not a.pingpong or (64<=a.frame_dma_stress<=512 and a.frame_dma_stress%2==0) or (a.play_pipeline and a.play_pipeline_test and a.wad_dma)
 assert not a.frame_dma_stress or (1<=a.frame_dma_stress<=2048 and a.doom_runtime and a.owned_mib==12 and a.upload_concurrent and not a.play_port and not a.play_dma_test)
 assert not a.play_frame_limit or (a.pingpong and a.wad_load_test and 100<=a.play_frame_limit<=1000 and a.play_frame_limit%2==0)
 assert a.release_schedule=="baseline" or (a.pingpong and a.play_pipeline_test)
 assert a.release_schedule not in ("abba","baab") or a.play_frame_limit>=520
 assert not a.wad_load_test or a.play_pipeline_test
 assert not a.wad_ring or (a.wad_dma and a.pingpong and a.play_pipeline_test)
 assert not a.wad_dma or a.play_pipeline
 assert not a.play_pipeline_test or a.play_pipeline
 assert not a.play_no_crc or (a.play_pipeline and not a.play_pipeline_test)
 assert not a.play_pipeline or (a.play_port and not (a.play_dma_test or a.play_bulk or a.play_bulk_test or a.play_accept_frames or a.frame_dma_stress))
 assert not a.play_dma_test or (a.play_port and not a.play_bulk_test and not a.play_accept_frames)
 assert not a.dma_stop or (a.dma_proof and not a.deadline)
 assert not a.dma_deadline_job or (a.dma_proof and a.deadline and not a.dma_stop)
 assert not (a.play_bulk_test and a.play_accept_frames), "bulk acceptance is one 28-frame session"
 assert not (a.play_bulk or a.play_bulk_test) or a.play_port
 assert not a.play_accept_frames or a.play_port
 if a.play_port:assert 1024<=a.play_port<=65535 and a.doom_runtime and a.owned_mib==12 and 0<=a.play_accept_frames<=100
 assert 3<=a.audit_interval<=60
 if a.owned_mib:assert a.queue_reclaim
 if a.play_port or a.frame_dma_stress:
  admission=json.loads((a.payload.parent/'entry/engine/manifest.json').read_text())
  from presentation_profile import preflight
  preflight(admission,a.play_pipeline,a.play_pipeline_test,a.wad_load_test)
  assert bool(admission.get('pingpong'))==a.pingpong, 'pingpong admission mismatch'
  assert bool(admission.get('dma_stress'))==bool(a.frame_dma_stress), 'producer/runner mismatch'
 if a.wad_ring:
  assert '-DI960_WAD_RING' in json.loads((a.payload.parent/'build.json').read_text())['flags'], 'rebuild for WAD ring'
  assert 'wad_ring_ioctl' in (a.module.parent/'dac960auto.c').read_text(), 'rebuild matching WAD ring driver'
 if a.wad_dma:
  assert '_wad_dma_isolation_snapshot' in (a.payload.parent/'kernel.map').read_text(), 'rebuild the resident kernel for bulk WAD support'
  assert 'wad_dma_ioctl' in (a.module.parent/'dac960auto.c').read_text(), 'rebuild the matching bulk WAD driver'
 flags=json.loads((a.payload.parent/'build.json').read_text())['flags']
 drain_telemetry='-DI960_PEER_YIELD' in flags and '_peer_drain_report' in (a.payload.parent/'kernel.symbols').read_text()
 if '-DI960_WAD_PROFILE' in flags:
  assert a.wad_ring and a.wad_load_test and a.audit_interval==3 and admission.get('wad_profile'), 'WAD profiling requires matching bounded engine and full audits'
 if a.pingpong:
  sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dma/stress'))
  sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dma/pingpong'))
  import pingpong_client # Import before taking hardware ownership.
 assert ('-DI960_DOOM_PLAY' in flags)==bool(a.play_port or a.frame_dma_stress), 'play image requires the interactive runner'
 assert ('-DI960_DOOM_DMA' in flags)==bool(a.play_dma_test or a.play_pipeline or a.frame_dma_stress)
 assert ('-DI960_DMA_PROOF' in flags)==a.dma_proof
 max_ticks,max_rounds,max_interval=traffic_limits(flags,a.owned_mib)
 assert 100<=a.ticks<=max_ticks and 1<=a.rounds<=max_rounds and 0<=a.round_interval<=max_interval
 owned_flags=[int(f.split('=')[1]) for f in flags if f.startswith('-DI960_OWNED_MIB=')]
 assert owned_flags==([a.owned_mib] if a.owned_mib else [])
 assert ('-DI960_RESIDENT_UPLOAD' in flags)==a.resident_upload
 assert ('-DI960_DOOM_HEAP' in flags)==a.doom_heap
 assert not a.doom_heap or a.resident_upload
 assert ('-DI960_DOOM_SHARED' in flags)==a.doom_shared
 assert not a.doom_shared or a.doom_heap
 assert ('-DI960_DOOM_RUNTIME' in flags)==a.doom_runtime
 assert not a.doom_runtime or (a.doom_shared and a.wad and a.upload_concurrent)
 runtime=(a.wad,a.payload.parent/'entry/runtime-probe.bin') if a.doom_runtime else None
 assert not a.upload_concurrent or a.resident_upload
 if a.queue_reclaim:assert a.heap_shared
 if a.heap_shared:assert a.general_heap
 if a.general_heap:assert a.extra_ram and a.fault_owner and a.secondary_reset
 if a.round_interval:assert (a.rounds-1)*a.round_interval+20<a.ticks/100
 b=Board(a.payload,a.module,a.output,autonomous=True,bdf=a.bdf);(b.out/'test-options.json').write_text(json.dumps(dict(play_frame_limit=a.play_frame_limit,release_schedule=a.release_schedule,wad_ring=a.wad_ring,pingpong=a.pingpong,wad_load_test=a.wad_load_test,wad_dma=a.wad_dma,play_pipeline=a.play_pipeline,play_pipeline_test=a.play_pipeline_test,play_no_crc=a.play_no_crc,frame_dma_stress=a.frame_dma_stress,play_dma_test=a.play_dma_test,dma_deadline_job=a.dma_deadline_job,dma_stop=a.dma_stop,dma_proof=a.dma_proof,play_bulk=a.play_bulk,play_bulk_test=a.play_bulk_test,play_port=a.play_port,play_accept_frames=a.play_accept_frames,audit_interval=a.audit_interval,doom_runtime=a.doom_runtime,doom_shared=a.doom_shared,doom_heap=a.doom_heap,upload_concurrent=a.upload_concurrent,resident_upload=a.resident_upload,control_journal_version=2,owned_mib=a.owned_mib,queue_reclaim=a.queue_reclaim,heap_shared=a.heap_shared,general_heap=a.general_heap,extra_ram=a.extra_ram,fault_owner=a.fault_owner,secondary_reset=a.secondary_reset,ticks=a.ticks,rounds=a.rounds,round_interval=a.round_interval,parallel=a.parallel,burst=a.burst,deadline=a.deadline,drop_data=a.drop_data),indent=2)+'\n');epoch=secrets.randbelow(65535)+1;events=[];snaps=[];diagnostics=[];packets=[];g=None;start=time.monotonic();pending_rx=None;traffic_active=False;drop={4,6} if a.drop_data else set();dropped=[]
 io_gate=IOGate();abort_upload=threading.Event()
 def save(final=False):
  if final:(b.out/'controls.json').write_text(json.dumps(events,indent=2)+'\n')
  (b.out/'snapshots.json').write_text(json.dumps(snaps,indent=2)+'\n')
 def record_control(event):
  events.append(event)
  with (b.out/'control-journal.jsonl').open('a') as journal:journal.write(json.dumps(event)+'\n')
 def control(op,arg=0,e=epoch):
  raw=bytearray(struct.pack('<8I',op,e,arg,0,0,0,0,0));started=time.monotonic_ns();fcntl.ioctl(b.fd,0xc0204d04,raw,True);w=list(struct.unpack('<8I',raw));event=dict(op=op,arg=arg,epoch=e,words=w,ns=time.monotonic_ns()-started);record_control(event)
  assert w[3]==1 and w[6:]==[0,0] and not w[4]&1;return w
 def frozen_page(page=0):
  # Only this main thread freezes the monitor's 64-word snapshot. UPL/WAD/
  # owned/network controls have independent buffers. Yield the host IO gate
  # between short read groups; do not delay a pending five-second WAD loan.
  with io_gate:control(7,page)
  words=[]
  for begin in range(0,64,4):
   # Keep packet pumping and sleep once per four words in both policies.
   # Only lock granularity changes; all 64 frozen words remain mandatory.
   step=1 if io_gate.priority_mode else 4
   for first in range(begin,begin+4,step):
    requested=time.monotonic_ns()
    with io_gate:
     acquired=time.monotonic_ns();words.extend(control(5,i)[2] for i in range(first,first+step));completed=time.monotonic_ns()
    with (b.out/'audit-gate.jsonl').open('a') as journal:journal.write(json.dumps(dict(page=page,begin=first,words=step,start_ns=requested,acquired_ns=acquired,end_ns=completed))+'\n')
   pump_packets() # keep TUN forwarding live while preserving the entire frozen page
   time.sleep(.001)
  return words
 def snapshot():
  w=frozen_page();snaps.append(dict(seconds=time.monotonic()-start,words=w));save()
  if a.owned_mib:
   m=frozen_page(2)
   with (b.out/'ram-diagnostics.jsonl').open('a') as f:f.write(json.dumps(dict(ticks=w[5],words=m))+'\n')
   if w[11] or any(m[40:]):abort_upload.set()
   validate_large(m,a.owned_mib,w[2]==2,transition=(w[3] in (1,2) or (a.deadline and w[5]>=a.ticks-100)));validate_large_stacks(w)
  assert w[0]==0x31525845 and w[2] in (1,2) and w[4]==w[11]==w[52]==0 and w[36:42]==[0]*6 and w[63]==(31 if a.general_heap else 15 if a.extra_ram else 7 if a.fault_owner else 3 if a.secondary_reset else 1)
  if a.secondary_reset:assert w[42:46]==[2,0,578,81916] and w[47]==0
  else:assert w[42:46]==[2,18,514,81916]
  assert w[54]==w[55] and w[56]==epoch
  if a.heap_shared and (not diagnostics or w[2]==2 or w[5]-diagnostics[-1]['ticks']>=1000):
   d=frozen_page(1);assert d[0]==0x314c5348 and d[54]==0 and d[55]==d[63]==1
   diagnostics.append(dict(seconds=time.monotonic()-start,ticks=w[5],words=d));(b.out/'heap-diagnostics.json').write_text(json.dumps(diagnostics,indent=2)+'\n')
  if drain_telemetry:
   d=frozen_page(3)
   with (b.out/'drain-diagnostics.jsonl').open('a') as f:f.write(json.dumps(dict(ticks=w[5],words=d))+'\n')
  print(json.dumps(dict(seconds=snaps[-1]['seconds'],state=w[2],ticks=w[5],work=w[6:8],queue=w[57:60],packets=w[60:63])),flush=True);return w
 def packet(op,data=b'',e=epoch):
  raw=bytearray(struct.pack('<8I',op,e,len(data),0,0,0,0,0)+data.ljust(1536,b'\0'));before=bytes(raw);t=time.monotonic_ns()
  try:fcntl.ioctl(b.fd,0xc6204d05,raw,True)
  except OSError as exc:
   record_control(dict(packet_op=op,errno=exc.errno,epoch=e,length=len(data)));save();raise
  w=list(struct.unpack_from('<8I',raw));assert w[3]==1 and not w[4]&1 and w[5:]==[0,0,0]
  if w[2]:
   record=dict(op=op,start_ns=t,ns=time.monotonic_ns()-t,request=before.hex(),response=raw.hex());append_packet(b.out,record);packets.append(record)
  return raw[32:32+w[2]]
 def pump_packets():
  nonlocal pending_rx
  if not traffic_active:return
  readable,_,_=select.select([g.fd],[],[],0)
  if pending_rx is None and readable:pending_rx=os.read(g.fd,1536)
  pending_rx=send_pending(packet,pending_rx)
  blob=packet(2);offset=0
  while offset<len(blob):
   n=struct.unpack_from('<I',blob,offset)[0];offset+=4;frame=blob[offset:offset+n];offset+=n;assert 20<=n<=1500 and len(frame)==n
   version=frame[0]>>4;ihl=20 if version==4 else 40;proto=frame[9] if version==4 else frame[6]
   if version in drop and proto==6 and struct.unpack_from('!H',frame,ihl)[0]==9600 and len(frame)>ihl+(frame[ihl+12]>>4)*4:
    drop.remove(version);dropped.append(dict(version=version,frame=frame.hex()));(b.out/'deliberate-loss.json').write_text(json.dumps(dropped,indent=2)+'\n');continue
   assert os.write(g.fd,frame)==n
  assert offset==len(blob)
 try:
  assert len(b.step(struct.pack('<4I',0x31415452,1,epoch,2|(a.ticks<<8))))==640
  for op,data,e in [(1,b'x'*20,epoch)]:
   try:packet(op,data,e);raise AssertionError('pre-resident packet accepted')
   except OSError as exc:assert exc.errno==errno.EBUSY
  control(4);w=snapshot();assert w[2]==1
  try:os.write(b.fd,wire.block(struct.pack('<4I',0x31415452,0,epoch,0),2));raise AssertionError('firmware callback accepted')
  except OSError as exc:assert exc.errno==errno.EIO;(b.out/'write-denied.txt').write_text('errno=5\n')
  for op,data,e,expected in [(1,b'x'*19,epoch,errno.EINVAL),(1,b'x'*1501,epoch,errno.EINVAL),(2,b'',epoch^0x8000 or 1,errno.ESTALE)]:
   try:packet(op,data,e);raise AssertionError('invalid packet accepted')
   except OSError as exc:assert exc.errno==expected
  time.sleep(.3);v=snapshot();assert v[5]>w[5] # timers advance without host packet traffic
  if a.resident_upload and not a.upload_concurrent:
   from upload_client import exercise
   print('Starting resident segmented upload tests',flush=True)
   exercise(b.fd,epoch,b.out,doom_heap=a.doom_heap,doom_shared=a.doom_shared);snapshot()
  if a.dma_proof:
   sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dma'))
   from client import exercise as dma_exercise
   dma_exercise(b.fd,epoch,b.out,snapshot)
  if a.burst:burst(packet,snapshot,b.out)
  g=Gateway(b.out,ipv6=True);traffic_active=True
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
   future=pool.submit(clients,a.rounds,a.parallel,a.round_interval,b.out);deadline=time.monotonic()+max(45,a.ticks/100-5);last=time.monotonic()
   upload_future=None
   def start_upload():
    from upload_client import exercise
    if a.frame_dma_stress:
     sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dma/stress'))
     if a.pingpong:
      sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dma/pingpong'))
      from pingpong_client import exercise as stress
     else:from stress_client import exercise as stress
     return pool.submit(stress,b.fd,epoch,b.out,io_gate,a.wad,a.payload.parent/'entry/engine',abort_upload,a.frame_dma_stress)
    elif a.play_port:
     from play_client import exercise as play
     return pool.submit(play,b.fd,epoch,b.out,io_gate,a.wad,a.payload.parent/'entry/engine',a.play_port,abort_upload,a.play_accept_frames,a.play_bulk,a.play_bulk_test,a.play_dma_test,a.play_pipeline,a.play_pipeline_test,a.play_no_crc,a.wad_dma,a.wad_load_test,a.pingpong,a.wad_ring,a.play_frame_limit,a.release_schedule)
    else:return pool.submit(exercise,b.fd,epoch,b.out,io_gate,a.doom_heap,a.doom_shared,runtime,abort_upload)
   # Complete the network proof before a large game upload can monopolize
   # the packet gate. The main loop still pumps packets and performs audits.
   upload_pending=a.upload_concurrent and bool(a.play_port or a.frame_dma_stress)
   if a.upload_concurrent and not upload_pending:upload_future=start_upload()
   while not future.done() or upload_pending or (upload_future is not None and not upload_future.done()):
    if time.monotonic()>deadline:raise TimeoutError('resident test exceeded session traffic budget')
    if (a.play_port or a.frame_dma_stress) and future.done():
     traffic_active=False
     if future.exception() is not None:
      # Do not enter executor shutdown while the engine keeps running and
      # periodic audits silently stop. Ask its owner to STOP, keep auditing,
      # then propagate the original network failure after the owner exits.
      abort_upload.set()
      (b.out/'network-error.txt').write_text(repr(future.exception())+'\n')
    if upload_pending and future.done():
     # Propagate the original error before admitting any engine upload.
     future.result()
     upload_future=start_upload();upload_pending=False
    pump_packets()
    if a.play_port or a.frame_dma_stress:time.sleep(.001)
    if time.monotonic()-last>a.audit_interval:snapshot();last=time.monotonic()
   traffic_active=False
   if upload_future is not None:upload_future.result()
   result=future.result();(b.out/'network-results.json').write_text(json.dumps(result,indent=2)+'\n')
  if a.dma_deadline_job:
   assert a.dma_proof and a.deadline and not a.dma_stop
   from client import stop_exercise
   before=time.monotonic();w=snapshot()
   delay=(a.ticks-w[5])*.01-(time.monotonic()-before)-.04
   assert delay>0, 'need a longer session for the deadline cancellation test'
   (b.out/'dma-deadline-plan.json').write_text(json.dumps(dict(tick=w[5],limit=a.ticks,delay=delay,lead_seconds=.04))+'\n')
   time.sleep(delay)
   stop_exercise(b.fd,epoch,b.out,lambda:time.sleep(.15),reason='deadline')
  elif a.dma_stop:
   from client import stop_exercise
   snapshot();stop_exercise(b.fd,epoch,b.out,lambda:control(6))
  elif not a.deadline:control(6)
  until=time.monotonic()+a.ticks/100+10
  while time.monotonic()<until:
   w=snapshot()
   if w[2]==2:break
   time.sleep(.5)
  assert w[2]==2 and w[3]==(2 if a.deadline else 1) and w[8:10]==[1,1] and w[12]==w[13]>0 and w[14]==w[15]>0 and w[53]==0
  for op,data in [(1,b'x'*20),(2,b'')]:
   try:packet(op,data);raise AssertionError('parked networking accepted')
   except OSError as exc:assert exc.errno==(errno.EAGAIN if op==1 else errno.ESHUTDOWN)
  v=snapshot();assert v[4:36]==w[4:36];control(6)
  if a.resident_upload:
   from upload_client import Upload
   q=Upload(b.fd,epoch,b.out).query()
   (b.out/'upload-parked.json').write_text(json.dumps(list(q))+'\n')
   (b.out/'last-control.txt').write_text((b.debugfs/'result.txt').read_text())
   assert q[3]==q[4]==q[15]==0
   if not (a.play_port or a.frame_dma_stress):assert q[9]==(15 if (b.out/"batch-results.json").exists() else 14 if (b.out/"engine-results.json").exists() else 12 if (b.out/"owned-results.json").exists() else 10 if (b.out/"cache-results.json").exists() else 8 if (b.out/"relocate-results.json").exists() else 4 if a.doom_runtime else 3)
  (b.out/'last-control.txt').write_text((b.debugfs/'result.txt').read_text())
  print('Resident network tests passed; module retained until reboot.',flush=True)
 except BaseException:
  try:
   control(7);failure_words=[control(5,i)[2] for i in range(64)]
   (b.out/'failure-snapshot.json').write_text(json.dumps(failure_words,indent=2)+'\n')
  except BaseException as diag_error:(b.out/'failure-snapshot-error.txt').write_text(repr(diag_error)+'\n')
  (b.out/'error.txt').write_text(traceback.format_exc());raise
 finally:
  save(final=True);finish_packets(b.out,packets)
  if g:g.close()
  if b.fd is not None:os.close(b.fd);b.fd=None;capture(b.out/'retained-close',b.debugfs)
  if b.records:b.records.close()
  if b.lock:b.lock.close()
if __name__=='__main__':main()
