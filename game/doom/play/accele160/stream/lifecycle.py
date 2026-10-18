#!/usr/bin/env python3
"""Physical gateway negative/lifetime gates; ends in audited reusable game STOP.

Run on Linux with no other keyboard controller. Uses browser APIs only.
"""
import asyncio
import json
import re
import time
import urllib.request
from websockets.asyncio.client import connect


async def main():
    def get(path):
        with urllib.request.urlopen('http://127.0.0.1:8088'+path,timeout=3) as r:return r.read()
    page=await asyncio.to_thread(get,'/')
    token=re.search(r"const token='([^']+)'",page.decode())[1]
    async def state():return json.loads(await asyncio.to_thread(get,'/status'))
    async def attach(path):
        ws=await connect('ws://127.0.0.1:8088'+path,proxy=None,compression=None,max_size=131072)
        await ws.send(json.dumps(dict(token=token)))
        return ws
    control=await attach('/input');ready=json.loads(await control.recv())
    run=ready['state']['run_id'];seq=0
    assert ready['state']['state']=='running'
    async def send(op,**kw):
        nonlocal seq
        seq+=1
        await control.send(json.dumps(dict(seq=seq,op=op,run_id=kw.pop('run_id',run),**kw)))
        reply=json.loads(await control.recv());assert reply['seq']==seq
        return reply
    async def wait_switch(count):
        deadline=time.monotonic()+3
        while True:
            s=await state()
            if s['flat_switches']==count:return s
            assert time.monotonic()<deadline,'switch deadline'
            await asyncio.sleep(.01)
    video=await attach('/video')
    first=json.loads(await video.recv());await video.recv()
    second=json.loads(await video.recv());await video.recv()
    before=await state();start=time.monotonic()
    await send('key',key=192,down=1);await send('key',key=192,down=0)
    await wait_switch(before['flat_switches']+1)
    stalled_input_ms=(time.monotonic()-start)*1000
    # Keep the independent control connection alive while deliberately starving
    # the two-credit video socket. The card must continue producing audited frames.
    while video.close_code is None:
        await send('heartbeat');await asyncio.sleep(.25)
        assert time.monotonic()-start<7,'stalled display did not close'
    assert video.close_code==1008
    after=await state();assert after['state']=='running' and after['frame']!=first['state']['frame']
    count=after['flat_switches']
    rejection=await send('key',key=192,down=1,run_id=run-1)
    assert rejection.get('error')=='stale game'
    await asyncio.sleep(.1);assert (await state())['flat_switches']==count
    # Disconnect after an accepted down, without sending up. A new press must
    # still toggle, proving the old connection's held key was released.
    await send('key',key=192,down=1);await wait_switch(count+1)
    await control.close();await asyncio.sleep(.3)
    control=await attach('/input');await control.recv();seq=0
    await send('key',key=192,down=1);await send('key',key=192,down=0)
    await wait_switch(count+2)
    await control.close();await asyncio.sleep(.1)
    bad=await attach('/input');await bad.recv()
    await bad.send(json.dumps(dict(seq=2,op='heartbeat',run_id=run)))
    await bad.wait_closed();assert bad.close_code==1008
    await asyncio.sleep(.1)
    control=await attach('/input');await control.recv();seq=0
    reply=await send('stop');assert 'error' not in reply
    deadline=time.monotonic()+30
    while (await state())['state']!='idle':
        assert time.monotonic()<deadline,'STOP idle deadline'
        await send('heartbeat');await asyncio.sleep(.1)
    final=await state();await control.close()
    print(json.dumps(dict(run_id=run,stalled_video_close_code=video.close_code,
        input_during_stall_ms=stalled_input_ms,stale_rejected=True,
        disconnect_release_confirmed=True,sequence_gap_rejected=True,final=final),indent=2))


if __name__=='__main__':asyncio.run(main())
