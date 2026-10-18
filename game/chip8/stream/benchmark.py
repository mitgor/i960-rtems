#!/usr/bin/env python3
"""Native transport timing, not card or browser paint performance."""
import asyncio,io,json,statistics,time
from server import NativeOwner,shared,HERE
from host import demo_rom
from codec import validate_frame,validate_payload
from websockets.asyncio.client import connect
from websockets.asyncio.server import serve
async def main():
 owner=NativeOwner(demo_rom());g=shared.Gateway(owner,io.StringIO(),allowed=range(16),frame_validator=validate_frame,page=HERE/'index.html',running_prefix='CHIP-8 on')
 async with serve(g.handler,'127.0.0.1',0,process_request=g.http,compression=None) as s:
  url='ws://127.0.0.1:'+str(s.sockets[0].getsockname()[1]);tasks=[asyncio.create_task(owner.run()),asyncio.create_task(g.poll())]
  try:
   async with connect(url+'/input',proxy=None) as keys,connect(url+'/video',proxy=None) as video:
    for ws in (keys,video):await ws.send(json.dumps(dict(token=g.token)))
    await keys.recv();times=[];lat=[];sent=None;down=0;seq=0
    for i in range(180):
     meta=json.loads(await video.recv());raw=await video.recv();q=validate_payload(raw[32:]);now=time.perf_counter();times.append(now)
     if sent is not None and bool(q['held']&16)==bool(down):lat.append((now-sent)*1000);sent=None
     await video.send(json.dumps(dict(frame=meta['state']['frame'])))
     if i%10==0:
      down^=1;seq+=1;sent=time.perf_counter()
      await keys.send(json.dumps(dict(seq=seq,op='key',run_id=1,key=4,down=down)));ack=json.loads(await keys.recv());assert 'error' not in ack
    print(json.dumps(dict(backend='native host simulation; no PCI; no browser paint',frames=len(times),fps=(len(times)-1)/(times[-1]-times[0]),key_to_observed_frame_ms_median=statistics.median(lat),key_to_observed_frame_ms_max=max(lat),input_samples=len(lat),packet_bytes=544,payload_bytes=512),indent=2))
  finally:
   for t in tasks:t.cancel()
   await asyncio.gather(*tasks,return_exceptions=True)
asyncio.run(main())
