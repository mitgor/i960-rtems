#!/usr/bin/env python3
"""Real gateway and real native CHIP-8 player: input/video/lifecycle tests."""
import asyncio,io,json,struct,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from server import NativeOwner,shared,HERE
from codec import validate_frame,validate_payload
from host import demo_rom
from websockets.asyncio.client import connect
from websockets.asyncio.server import serve

async def main():
 owner=NativeOwner(demo_rom());g=shared.Gateway(owner,io.StringIO(),allowed=range(16),frame_validator=validate_frame,page=HERE/'index.html',running_prefix='CHIP-8 on')
 async with serve(g.handler,'127.0.0.1',0,process_request=g.http,max_size=1024,max_queue=16,compression=None,close_timeout=.1) as s:
  url=f'ws://127.0.0.1:{s.sockets[0].getsockname()[1]}'
  model=asyncio.create_task(owner.run());poll=asyncio.create_task(g.poll())
  async def attach(path):
   ws=await connect(url+path,proxy=None,compression=None);await ws.send(json.dumps(dict(token=g.token)));return ws
  async def command(ws,seq,op,run=1,**body):
   await ws.send(json.dumps(dict(seq=seq,op=op,run_id=run,**body)));return json.loads(await asyncio.wait_for(ws.recv(),2))
  try:
   control=await attach('/input');assert json.loads(await control.recv())['type']=='ready'
   video=await attach('/video')
   async def frame():
    meta=json.loads(await asyncio.wait_for(video.recv(),2));raw=await video.recv();epoch,n=validate_frame(raw)
    assert meta['state']['frame']==f'{epoch}-{n}'
    return meta,raw
   meta,raw=await frame();await video.send(json.dumps(dict(frame=meta['state']['frame'])))
   result=await command(control,1,'key',key=4,down=1);assert 'error' not in result
   for _ in range(20):
    meta,raw=await frame();q=validate_payload(raw[32:]);await video.send(json.dumps(dict(frame=meta['state']['frame'])))
    if q['held']==16:break
   else:raise AssertionError('key never reached player')
   await control.close()
   for _ in range(20):
    meta,raw=await frame();q=validate_payload(raw[32:]);await video.send(json.dumps(dict(frame=meta['state']['frame'])))
    if not q['held']:break
   else:raise AssertionError('disconnect failed to release key')
   control=await attach('/input');await control.recv()
   # Stop acknowledging video: exactly two pending frames cannot block input.
   await frame();await frame()
   assert 'error' not in await command(control,1,'stop')
   assert owner.stopped
   result=await command(control,2,'key',key=2,down=1);assert 'error' in result
   assert 'error' not in await command(control,3,'restart')
   assert owner.run_id==2
   stale=await command(control,4,'key',run=1,key=2,down=1);assert stale['error']=='stale game'
   await control.close();await video.close()
   for offset in (0,4,16,24,32,32+304,32+336):
    bad=bytearray(raw);bad[offset]^=0xff
    try:validate_frame(bad)
    except ValueError:pass
    else:raise AssertionError(f'mutated frame accepted: {offset}')
   print('PASS CHIP-8 stream: real player, key/down/up, disconnect release, two-credit stalled video, STOP/restart/stale isolation, frame mutations')
  finally:
   model.cancel();poll.cancel();await asyncio.gather(model,poll,return_exceptions=True)
asyncio.run(main())
