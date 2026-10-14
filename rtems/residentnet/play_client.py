"""Interactive Doom relay; only the upload worker accesses card ioctls.
HTTP threads exchange bounded keys and immutable PNG/binary bytes, never card RAM.
"""
import errno,hashlib,json,secrets,struct,threading,time,zlib
from collections import deque
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from batch_client import BatchServer
from owned_client import Control
from frame_client import png

def exercise(fd,epoch,out,gate,wad,root,port,abort,accept_frames=0,bulk=False,bulk_test=False,dma_test=False,pipeline=False,pipeline_test=False,no_crc=False,wad_dma=False,wad_load_test=False):
 from upload_client import Upload
 u=Upload(fd,epoch,out,gate,abort);root=Path(root);out=Path(out)
 m=json.loads((root/'manifest.json').read_text());assert m['startup']['play']
 assert bool(m.get('double_buffer'))==pipeline, 'pipeline requires the admitted two-buffer engine'
 blob=(root/'template.bin').read_bytes();meta=(root/'relocations.bin').read_bytes()
 assert hashlib.sha256(blob).hexdigest()==m['template_sha256'] and hashlib.sha256(meta).hexdigest()==m['metadata_sha256']
 profile=bool(m.get('frame_profile'));presentation_test=bool(m.get('presentation_test') or m.get('detail_test') or m.get('column_test'))
 if presentation_test:assert pipeline_test and not wad_load_test
 if profile:
  assert pipeline
  (out/'presentation-options.json').write_text(json.dumps({k:m.get(k,False) for k in ('frame_profile','no_fnv','direct_frame','presentation_test','low_detail','detail_test','cpu_profile','column_test')})+'\n')
 token=secrets.token_hex(24);lock=threading.Lock();keys=deque();stop=threading.Event();held_keys=set();input_deadline=[0.]
 dma=None
 if dma_test or pipeline:
  import sys
  sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dma'))
  from frame_dma_client import FrameDMA
  dma=FrameDMA(fd,epoch,out,gate)
 state=dict(frame='',binary=pipeline, message='Starting the RTEMS Doom runtime…');image=b'';binary=b''
 page=(Path(__file__).resolve().parents[2]/'game/doom/play/index.html').read_text().replace('__TOKEN__',token).encode()
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def reply(self,code,data,kind='application/json'):
   self.send_response(code);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers()
   try:self.wfile.write(data)
   except (BrokenPipeError,ConnectionResetError):pass
  def do_GET(self):
   with lock:
    if self.path=='/':data,kind=page,'text/html; charset=utf-8'
    elif self.path=='/status':data,kind=json.dumps(state).encode(),'application/json'
    elif self.path.startswith('/frame.png?') and not pipeline:data,kind=image,'image/png'
    elif self.path.startswith('/frame.bin?') and pipeline:data,kind=binary,'application/octet-stream'
    else:self.reply(404,b'not found','text/plain');return
   self.reply(200,data,kind)
  def do_POST(self):
   if self.headers.get('X-Session-Token')!=token or self.headers.get('Origin') not in (None,'http://'+self.headers.get('Host','')):self.reply(403,b'forbidden');return
   try:
    n=int(self.headers.get('Content-Length','0'));assert 0<n<=128
    b=json.loads(self.rfile.read(n))
    if self.path=='/stop':stop.set()
    elif self.path=='/heartbeat':
     with lock:input_deadline[0]=time.monotonic()+3
    elif self.path=='/key':
     assert type(b['key']) is int and b['key'] in (173,175,172,174,163,162,182,13,27,9,121,110,49,50,51,52,53,54,55) and type(b['down']) is int and b['down'] in (0,1)
     with lock:
      if len(keys)>=128:stop.set();self.reply(429,b'key queue full; stopping to release all keys');return
      keys.append(b['key']+(b['down']<<8));input_deadline[0]=time.monotonic()+3
      if b['down']:held_keys.add(b['key'])
      else:held_keys.discard(b['key'])
    else:self.reply(404,b'not found');return
   except (ValueError,KeyError,AssertionError):self.reply(400,b'invalid request');return
   self.reply(200,b'{}')
 http=ThreadingHTTPServer(('0.0.0.0',port),Handler);threading.Thread(target=http.serve_forever,daemon=True).start()
 def message(s):
  with lock:state['message']=s
  print(s,flush=True)
 if wad_dma:
  from wad_dma_client import BulkServer
  server=BulkServer(u,wad)
 else:server=BatchServer(u,wad)
 def ctl(i=0,v=0):return struct.unpack('<I',u.io(10,struct.pack('<2I',i,v)))[0]
 try:
  # Preserve the proven 1 MiB placement gap while establishing both heap owners.
  u.begin([(0,4,4,1,0),(16,0,1048576-16,2,0)]);assert u.command(8)[5]==0x444c4942;u.command(5)
  u.command(10,data=struct.pack('<3I',0x31444157,1,len(server.data))+bytes.fromhex(server.sha))
  for session in range(2 if accept_frames and not (bulk_test or dma_test) else 1):
   stop.clear();seen=0;control=Control(u,False);started=time.monotonic();last_poll=0;stop_sent=False;request_base=len(server.records);last_loading_message=0
   parts=[blob[s['offset']:s['offset']+s['file_bytes']] for s in m['sections']]+[meta]
   geometry=[(s['offset'],s['file_bytes'],s['memory_bytes'],s['flags']) for s in m['sections']]+[(m['metadata_offset'],len(meta),len(meta),2)]
   message('Uploading Doom engine…')
   u.begin([(*s,zlib.crc32(p)) for s,p in zip(geometry,parts)],m['entry'])
   for i,p in enumerate(parts):
    if p:u.write(i,p)
   u.prepare();engine_ready=time.monotonic();message('Loading the first level on the i960; please wait…')
   def serve():
    nonlocal image,binary,seen,last_poll,stop_sent,last_loading_message
    if abort is not None and abort.is_set():stop.set()
    if stop.is_set() and not stop_sent and (seen or len(server.records)>request_base):
     q=control.query()
     if q[2]:control.request(q[1]);stop_sent=True
    # Never race frame teardown after an owned STOP request.
    if stop_sent:return False
    # WAD requests must be serviced promptly even during startup.
    if server.serve():
     if not seen and time.monotonic()-last_loading_message>=2:
      last_loading_message=time.monotonic()
      with lock:state['message']=f'Loading the first level on the i960 · {len(server.records)-request_base:,} WAD blocks received · {time.monotonic()-engine_ready:.0f}s'
     return True
    if time.monotonic()-last_poll<.01:return False
    last_poll=time.monotonic();g=ctl()
    if g==0xffffffff:raise RuntimeError('interactive frame channel refused')
    if not g or g==seen:return False
    def read_frame(op):
     t=time.monotonic();data=b''.join(u.io(op,struct.pack('<2I',g,off)) for off in range(0,65536,1024))
     assert len(data)==65536 and data[:1024]==u.io(op,struct.pack('<2I',g,0))
     assert ctl()==g, 'frame expired during transfer; never ACK uncertain bytes'
     return data,time.monotonic()-t
    if (dma_test or pipeline_test) and g==1:
     for op,generation,offset,expected in ((1,g+1,0,errno.ESTALE),(3,g,73728,errno.EINVAL),(3,g,4,errno.EINVAL)):
      try:dma.call(op,generation,offset);raise AssertionError("invalid DMA frame request accepted")
      except OSError as e:assert e.errno==expected
    if bulk_test and g==1:
     for generation,offset,expected in ((g+1,0,errno.ESTALE),(g,65536,errno.EINVAL),(g,4,errno.EINVAL)):
      try:u.io(11,struct.pack('<2I',generation,offset));raise AssertionError('invalid bulk request accepted')
      except OSError as e:assert e.errno==expected
    begin=time.monotonic();method=11 if bulk else 9;comparison=None
    # Four same-frame comparisons followed by scalar/bulk/bulk/scalar blocks.
    # Full snapshot/RAM audits continue independently at the unchanged interval.
    if bulk_test:method=11 if g<=4 or 11<=g<=22 else 9
    if dma_test:method=12 if g<=4 or 11<=g<=22 else 11
    if pipeline:method=12
    crc=not no_crc
    if pipeline_test:crc=False if presentation_test else g<=2 or 5<=g<=16 or g>=41
    raw,transfer_seconds=(dma.read(g,crc,server.serve) if pipeline else dma.read(g)) if method==12 else read_frame(method)
    if method==12:assert ctl()==g, 'DMA frame expired; never ACK uncertain bytes'
    if (dma_test or pipeline_test) and g<=4:
     other,other_seconds=read_frame(11);assert other==raw, 'DMA/mailbox frame mismatch'
     comparison=dict(mailbox_seconds=other_seconds,dma_seconds=transfer_seconds,bytes=65536)
    if bulk_test and g<=4:
     other,other_seconds=read_frame(9)
     assert other==raw, 'bulk and scalar frame bytes differ'
     comparison=dict(scalar_seconds=other_seconds,bulk_seconds=transfer_seconds,bytes=65536)
    profile_begin=time.monotonic();profile_row=None
    if profile:
     from presentation_profile import decode
     profile_row=decode(raw,g,m.get('presentation_test',False),m)
     timing=[ctl(7,i) for i in range(5)]
     assert timing[0]==g and timing[4]==sum(timing[1:4]) and all(x<60000 for x in timing[1:])
     profile_row['dma']=dict(zip(('frame','prepare_ms','hardware_ms','cleanup_ms','total_ms'),timing))
    convert=time.monotonic()
    picture=b'' if pipeline else png(raw);png_seconds=time.monotonic()-convert
    packet=struct.pack('<8I',0x31424644,1,session,g,320,200,65536,int(crc))+raw if pipeline else b''
    # Send input through the bounded IRQ FIFO; a full card queue keeps
    # remaining host keys for the next frame, including release events.
    with lock:
     if held_keys and time.monotonic()>input_deadline[0]:
      keys.extend(sorted(held_keys));held_keys.clear()
     while keys:
      if ctl(2,keys[0])!=0:break
      keys.popleft()
    if (accept_frames or bulk_test or dma_test) and session==0:
     if g==2:assert ctl(2,256+173)==0
     if g==4:assert ctl(2,173)==0
    if wad_load_test and g in (10,12,14,16):
     key=27 if g==10 else 13
     assert ctl(2,256+key)==0 and ctl(2,key)==0
    assert ctl(1,g)==0;seen=g
    row=dict(wad_requests=len(server.records)-request_base,engine_seconds=time.monotonic()-engine_ready,crc=crc,binary=pipeline,method=method,comparison=comparison,transfer_seconds=transfer_seconds,png_seconds=png_seconds,session=session,frame=g,seconds=time.monotonic()-started,readback_seconds=time.monotonic()-begin,sha256=hashlib.sha256(raw).hexdigest())
    if profile:row['profile']=profile_row;row['profile_read_seconds']=convert-profile_begin
    with (out/'play-frames.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
    if g<=8 or bulk_test or dma_test or pipeline_test:
     (out/f'play-{session}-{g}.bin').write_bytes(raw)
     if not pipeline:(out/f'play-{session}-{g}.png').write_bytes(picture)
     else:(out/f'play-{session}-{g}.dfb').write_bytes(packet)
    with lock:image=picture;binary=packet;state.update(frame=f'{session}-{g}',message=f'Live i960 Doom · frame {g} · readback {row["readback_seconds"]:.2f}s · click game for keyboard')
    print(json.dumps(row),flush=True)
    if (pipeline_test and g>=52) or ((bulk_test or dma_test) and g>=28) or (accept_frames and session==0 and g>=accept_frames):stop.set()
    return False
   u.service=serve
   try:reply=u.command(18,timeout=3660)
   finally:u.service=None
   result=[u.command(19,i)[5] for i in range(12)];assert reply[5]==0x454e4702 and result[9:]==[2,1,210],result
   with (out/'play-sessions.jsonl').open('a') as f:f.write(json.dumps(dict(session=session,result=result,reply=list(reply)))+'\n')
   message('Doom stopped cleanly.' if session or not accept_frames else ('Input/STOP test passed; starting your play session…' if seen>=accept_frames else 'Startup STOP completed; loading a fresh session…'))
 finally:
  # Save immutable file identity and service counts, excluding visitor data.
  (out/'play-wad.json').write_text(json.dumps(dict(sha256=server.sha,bytes=len(server.data),requests=len(server.records)))+'\n')
  http.shutdown();http.server_close()
