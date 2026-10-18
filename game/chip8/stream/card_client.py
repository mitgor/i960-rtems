#!/usr/bin/env python3
"""Opt-in real card gateway acceptance; preserves owner for further play."""
import argparse,asyncio,json,re,time,statistics,urllib.request
from websockets.asyncio.client import connect
from codec import validate_frame,validate_payload
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--url',default='http://192.168.2.75:8096');p.add_argument('--out');p.add_argument('--games',type=int,default=3);p.add_argument('--frames',type=int,default=150);a=p.parse_args()
def get(path):
 with urllib.request.urlopen(a.url+path,timeout=3) as r:return r.read()
async def main():
 token=re.search(r"const token='([^']+)'",get('/').decode()).group(1);url=a.url.replace('http','ws',1);seq=0;results=[]
 async with connect(url+'/input',proxy=None,compression=None) as control:
  await control.send(json.dumps(dict(token=token)));await control.recv()
  async def command(op,run,**body):
   nonlocal seq
   seq+=1;await control.send(json.dumps(dict(seq=seq,op=op,run_id=run,**body)));return json.loads(await asyncio.wait_for(control.recv(),3))
  async def state(want):
   for _ in range(200):
    s=json.loads(get('/status'))
    if s['state']==want:return s
    await asyncio.sleep(.05)
   raise RuntimeError('owner state deadline '+want)
  for game in range(a.games):
   s=await state('running');run=s['run_id'];times=[];lat=[];pending=None;down=0
   async with connect(url+'/video',proxy=None,compression=None) as video:
    await video.send(json.dumps(dict(token=token)))
    for i in range(a.frames):
     meta=json.loads(await asyncio.wait_for(video.recv(),4));raw=await video.recv();validate_frame(raw);q=validate_payload(raw[32:]);now=time.perf_counter();times.append(now)
     assert meta['state']['run_id']==run
     if pending is not None and bool(q['held']&16)==bool(down):lat.append((now-pending)*1000);pending=None
     await video.send(json.dumps(dict(frame=meta['state']['frame'])))
     if i==a.frames-20:
      assert 'error' not in await command('keys',run,events=[261,5]*8)
     if i%12==0:
      down^=1;pending=time.perf_counter();r=await command('key',run,key=4,down=down);assert 'error' not in r
    r=dict(run_id=run,frames=len(times),gateway_delivered_fps=(len(times)-1)/(times[-1]-times[0]),key_to_observed_frame_ms_median=statistics.median(lat),key_to_observed_frame_ms_max=max(lat),samples=len(lat),stalled_video_input_stop=False)
    results.append(r)
    if a.out:open(a.out,'w').write(json.dumps(dict(games=results,final_state='testing'),indent=2)+'\n')
    await command('key',run,key=4,down=0)
    # Withhold both video credits: input and STOP must still work.
    for _ in range(2):await video.recv();await video.recv()
    await asyncio.sleep(.2)
    assert 'error' not in await command('key',run,key=6,down=1)
    assert 'error' not in await command('key',run,key=6,down=0)
    assert 'error' not in await command('stop',run)
   idle=await state('idle')
   r['stalled_video_input_stop']=True
   if a.out:open(a.out,'w').write(json.dumps(dict(games=results,final_state='idle'),indent=2)+'\n')
   if game+1<a.games:
    assert 'error' not in await command('restart',run)
    await state('running')
    stale=await command('key',run,key=2,down=1);assert stale.get('error')=='stale game'
  print(json.dumps(dict(backend='physical AcceleRAID 160 via LAN WebSockets; excludes browser paint',games=results,final_state='idle'),indent=2))
asyncio.run(main())
