#!/usr/bin/env python3
"""Exercise production gateway against the real HTTP BrowserSession, without PCI."""
import asyncio
import io
import json
from pathlib import Path
import struct
import sys
import urllib.request

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed, InvalidStatus
from gateway import Gateway, Owner, validate_frame

sys.path.insert(0,str(Path(__file__).resolve().parents[5]/'rtems/accele160/doom_dma'))
from browser import BrowserSession


class TestOwner(Owner):
    def __init__(self, browser):
        self.base=f'http://127.0.0.1:{browser.port}'
        self.identity=dict(token=browser.token)
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def check(self): pass


async def main():
    browser=BrowserSession(0,runtime_flat=True)
    journal=io.StringIO()
    gateway=Gateway(TestOwner(browser),journal)
    async with serve(gateway.handler,'127.0.0.1',0,process_request=gateway.http,
                     max_size=1024,max_queue=16,compression=None,close_timeout=.1) as server:
        port=server.sockets[0].getsockname()[1]
        base=f'ws://127.0.0.1:{port}'
        poll=asyncio.create_task(gateway.poll())
        async def attach(path, token=None):
            ws=await connect(base+path,proxy=None,compression=None)
            await ws.send(json.dumps(dict(token=gateway.token if token is None else token)))
            return ws
        async def message(ws,seq,op='key',run_id=1,**kw):
            await ws.send(json.dumps(dict(seq=seq,op=op,run_id=run_id,**kw)))
            return json.loads(await ws.recv())
        async def frame(ws):
            meta=json.loads(await asyncio.wait_for(ws.recv(),2))
            packet=await ws.recv()
            epoch,generation=validate_frame(packet)
            assert meta['state']['frame']==f'{epoch}-{generation}'
            return meta,packet
        try:
            try:
                async with connect(base+'/input',origin='http://evil.invalid',proxy=None):
                    raise AssertionError('cross-origin accepted')
            except InvalidStatus as error: assert error.response.status_code==403
            bad=await attach('/input','bad')
            await bad.wait_closed();assert bad.close_code==1008
            control=await attach('/input');assert json.loads(await control.recv())['type']=='ready'
            duplicate=await attach('/input');await duplicate.wait_closed();assert duplicate.close_code==1008
            stale=await message(control,1,key=173,down=1,run_id=0)
            assert stale['error']=='stale game' and browser.next_key() is None
            assert 'error' not in await message(control,2,key=173,down=1)
            assert browser.next_key()==429
            assert 'error' not in await message(control,3,key=173,down=0)
            assert browser.next_key()==173
            video=await attach('/video')
            data=bytes(65536)
            browser.publish(1,data,dict(flat_planes=0,flat_switches=0))
            first,_=await frame(video)
            browser.publish(2,data,dict(flat_planes=0,flat_switches=0))
            second,_=await frame(video)
            for generation in range(3,11):
                browser.publish(generation,data,dict(flat_planes=0,flat_switches=0))
                await asyncio.sleep(.015)
            try:
                await asyncio.wait_for(video.recv(),.06)
                raise AssertionError('more than two unacknowledged frames')
            except asyncio.TimeoutError:pass
            # Input and STOP must remain responsive while video credits are full.
            assert 'error' not in await message(control,4,key=174,down=1)
            assert browser.next_key()==430
            await video.send(json.dumps(dict(frame=first['state']['frame'])))
            latest,_=await frame(video);assert latest['state']['frame'].endswith('-10')
            await video.send(json.dumps(dict(frame='wrong-identity')))
            await video.wait_closed();assert video.close_code==1008
            await asyncio.sleep(.03)
            assert gateway.latest is None
            # Publishing with no viewer must not leave an old cached frame for
            # the next connection to mistake for its current input baseline.
            browser.publish(11,data,dict(flat_planes=1,flat_switches=1))
            video=await attach('/video')
            fresh,_=await frame(video);assert fresh['state']['frame'].endswith('-11')
            assert fresh['state']['flat_switches']==1
            await video.close()
            await control.close()
            await asyncio.sleep(.05);assert browser.next_key()==174
            # Strict ordering rejects missing messages, never silently drops edges.
            control=await attach('/input');await control.recv()
            await control.send(json.dumps(dict(seq=2,op='heartbeat',run_id=1)))
            await control.wait_closed();assert control.close_code==1008
            control=await attach('/input');await control.recv()
            assert 'error' not in await message(control,1,'stop')
            assert browser.stop.is_set()
            browser.idle(1)
            restart=await message(control,2,'restart')
            assert 'error' not in restart and browser.restart.is_set() and restart['state']['state']=='reloading'
            browser.begin_game(2)
            assert (await message(control,3,'stop',run_id=1))['error']=='stale game'
            assert not browser.stop.is_set()
            await control.close()
            for _ in range(100):
                if gateway.controller is None:break
                await asyncio.sleep(.01)
            assert gateway.controller is None
            # Every malformed packet fails before browser delivery.
            packet=struct.pack('<8I',0x31424644,1,1,1,320,200,65536,0)+data
            validate_frame(packet)
            for offset in (0,4,8,12,16,20,24):
                bad=bytearray(packet);struct.pack_into('<I',bad,offset,0)
                try:validate_frame(bad);raise AssertionError(offset)
                except ValueError:pass
            assert max(json.loads(line).get('inflight',0) for line in journal.getvalue().splitlines())<=2
            print('PASS authentication/origin, ordered keys, stale games, disconnect releases, two-credit latest frames, independent input, STOP/rearm, packet mutations')
        finally:
            gateway.closed.set();poll.cancel();await asyncio.gather(poll,return_exceptions=True)
            browser.close()


asyncio.run(main())
