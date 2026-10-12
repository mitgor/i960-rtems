#!/usr/bin/env python3
"""Reboot-only resident IPv4/IPv6 test; never sends a second firmware callback."""
import threading
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
 p=argparse.ArgumentParser()
 for n in ['payload','module','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--resident-upload',action='store_true')
 p.add_argument('--doom-heap',action='store_true')
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
 p.add_argument('--deadline',action='store_true');p.add_argument('--drop-data',action='store_true');a=p.parse_args();assert 100<=a.ticks<=(360000 if a.owned_mib else 180000) and 1<=a.rounds<=60 and 0<=a.round_interval<=60
 if a.owned_mib:assert a.queue_reclaim
 flags=json.loads((a.payload.parent/'build.json').read_text())['flags']
 owned_flags=[int(f.split('=')[1]) for f in flags if f.startswith('-DI960_OWNED_MIB=')]
 assert owned_flags==([a.owned_mib] if a.owned_mib else [])
 assert ('-DI960_RESIDENT_UPLOAD' in flags)==a.resident_upload
 assert ('-DI960_DOOM_HEAP' in flags)==a.doom_heap
 assert not a.doom_heap or a.resident_upload
 assert not a.upload_concurrent or a.resident_upload
 if a.queue_reclaim:assert a.heap_shared
 if a.heap_shared:assert a.general_heap
 if a.general_heap:assert a.extra_ram and a.fault_owner and a.secondary_reset
 if a.round_interval:assert (a.rounds-1)*a.round_interval+20<a.ticks/100
 b=Board(a.payload,a.module,a.output,autonomous=True);(b.out/'test-options.json').write_text(json.dumps(dict(doom_heap=a.doom_heap,upload_concurrent=a.upload_concurrent,resident_upload=a.resident_upload,control_journal_version=2,owned_mib=a.owned_mib,queue_reclaim=a.queue_reclaim,heap_shared=a.heap_shared,general_heap=a.general_heap,extra_ram=a.extra_ram,fault_owner=a.fault_owner,secondary_reset=a.secondary_reset,ticks=a.ticks,rounds=a.rounds,round_interval=a.round_interval,parallel=a.parallel,burst=a.burst,deadline=a.deadline,drop_data=a.drop_data),indent=2)+'\n');epoch=secrets.randbelow(65535)+1;events=[];snaps=[];diagnostics=[];packets=[];g=None;start=time.monotonic();pending_rx=None;drop={4,6} if a.drop_data else set();dropped=[]
 io_gate=threading.RLock()
 def save(final=False):
  if final:(b.out/'controls.json').write_text(json.dumps(events,indent=2)+'\n')
  (b.out/'snapshots.json').write_text(json.dumps(snaps,indent=2)+'\n')
 def record_control(event):
  events.append(event)
  with (b.out/'control-journal.jsonl').open('a') as journal:journal.write(json.dumps(event)+'\n')
 def control(op,arg=0,e=epoch):
  raw=bytearray(struct.pack('<8I',op,e,arg,0,0,0,0,0));started=time.monotonic_ns();fcntl.ioctl(b.fd,0xc0204d04,raw,True);w=list(struct.unpack('<8I',raw));event=dict(op=op,arg=arg,epoch=e,words=w,ns=time.monotonic_ns()-started);record_control(event)
  assert w[3]==1 and w[6:]==[0,0] and not w[4]&1;return w
 def snapshot():
  with io_gate:return snapshot_locked()
 def snapshot_locked():
  control(7);w=[control(5,i)[2] for i in range(64)];snaps.append(dict(seconds=time.monotonic()-start,words=w));save()
  if a.owned_mib:
   control(7,2);m=[control(5,i)[2] for i in range(64)]
   with (b.out/'ram-diagnostics.jsonl').open('a') as f:f.write(json.dumps(dict(ticks=w[5],words=m))+'\n')
   validate_large(m,a.owned_mib,w[2]==2,transition=(w[3] in (1,2) or (a.deadline and w[5]>=a.ticks-100)));validate_large_stacks(w)
  assert w[0]==0x31525845 and w[2] in (1,2) and w[4]==w[11]==w[52]==0 and w[36:42]==[0]*6 and w[63]==(31 if a.general_heap else 15 if a.extra_ram else 7 if a.fault_owner else 3 if a.secondary_reset else 1)
  if a.secondary_reset:assert w[42:46]==[2,0,578,81916] and w[47]==0
  else:assert w[42:46]==[2,18,514,81916]
  assert w[54]==w[55] and w[56]==epoch
  if a.heap_shared and (not diagnostics or w[2]==2 or w[5]-diagnostics[-1]['ticks']>=1000):
   control(7,1);d=[control(5,i)[2] for i in range(64)];assert d[0]==0x314c5348 and d[54]==0 and d[55]==d[63]==1
   diagnostics.append(dict(seconds=time.monotonic()-start,ticks=w[5],words=d));(b.out/'heap-diagnostics.json').write_text(json.dumps(diagnostics,indent=2)+'\n')
  print(json.dumps(dict(seconds=snaps[-1]['seconds'],state=w[2],ticks=w[5],work=w[6:8],queue=w[57:60],packets=w[60:63])),flush=True);return w
 def packet(op,data=b'',e=epoch):
  raw=bytearray(struct.pack('<8I',op,e,len(data),0,0,0,0,0)+data.ljust(1536,b'\0'));before=bytes(raw);t=time.monotonic_ns()
  try:fcntl.ioctl(b.fd,0xc6204d05,raw,True)
  except OSError as exc:
   record_control(dict(packet_op=op,errno=exc.errno,epoch=e,length=len(data)));save();raise
  w=list(struct.unpack_from('<8I',raw));assert w[3]==1 and not w[4]&1 and w[5:]==[0,0,0]
  if w[2]:
   record=dict(op=op,ns=time.monotonic_ns()-t,request=before.hex(),response=raw.hex());append_packet(b.out,record);packets.append(record)
  return raw[32:32+w[2]]
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
   exercise(b.fd,epoch,b.out,doom_heap=a.doom_heap);snapshot()
  if a.burst:burst(packet,snapshot,b.out)
  g=Gateway(b.out,ipv6=True)
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
   future=pool.submit(clients,a.rounds,a.parallel,a.round_interval,b.out);deadline=time.monotonic()+max(45,a.ticks/100-5);last=time.monotonic()
   upload_future=None
   if a.upload_concurrent:
    from upload_client import exercise
    upload_future=pool.submit(exercise,b.fd,epoch,b.out,io_gate,a.doom_heap)
   while not future.done() or (upload_future is not None and not upload_future.done()):
    if time.monotonic()>deadline:raise TimeoutError('resident test exceeded session traffic budget')
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
    if time.monotonic()-last>3:snapshot();last=time.monotonic()
   if upload_future is not None:upload_future.result()
   result=future.result();(b.out/'network-results.json').write_text(json.dumps(result,indent=2)+'\n')
  if not a.deadline:control(6)
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
   q=Upload(b.fd,epoch,b.out).query();assert q[3]==q[4]==q[15]==0 and q[9]==3
   (b.out/'upload-parked.json').write_text(json.dumps(list(q))+'\n')
  (b.out/'last-control.txt').write_text((b.debugfs/'result.txt').read_text())
  print('Resident network tests passed; module retained until reboot.',flush=True)
 except BaseException:
  (b.out/'error.txt').write_text(traceback.format_exc());raise
 finally:
  save(final=True);finish_packets(b.out,packets)
  if g:g.close()
  if b.fd is not None:os.close(b.fd);b.fd=None;capture(b.out/'retained-close',b.debugfs)
  if b.records:b.records.close()
  if b.lock:b.lock.close()
if __name__=='__main__':main()
