#!/usr/bin/env python3
"""Matched HTTP/persistent F6-to-received-frame probes. No canvas paint claim.

Run on Linux (loopback) or the browser's computer. Injects eight F6 pulses per
mode, restoring the initial mode. Never run while a person is playing.
"""
import argparse
import asyncio
import hashlib
import json
import re
import statistics
import struct
import sys
import time
import urllib.request

from websockets.asyncio.client import connect


async def trial(mode, host, trials):
    owner=f'http://{host}:8087'
    gateway=f'http://{host}:8088'
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def get(url):
        with opener.open(url,timeout=5) as r:return r.read()
    def post(url,token,body):
        req=urllib.request.Request(url,json.dumps(body).encode(),
            headers={'X-Session-Token':token,'Content-Type':'application/json'})
        with opener.open(req,timeout=5) as r:return r.read()
    token=re.search(r"const token='([^']+)'",(await asyncio.to_thread(get,(owner if mode=='http' else gateway)+'/')).decode())[1]
    state=json.loads(await asyncio.to_thread(get,owner+'/status'))
    assert state['state']=='running' and state['flat_planes'] is not None
    run_id=state['run_id']
    frames=[];pulses=[];acks=[];latest=None;seq=0;sent={}
    stop=asyncio.Event()
    control=video=None
    def observe(packet):
        nonlocal latest
        assert len(packet)==65568
        header=struct.unpack_from('<8I',packet)
        assert header[0:2]==(0x31424644,1) and header[4:]==(320,200,65536,0)
        magic,version,flat,switches=struct.unpack_from('<4I',packet,32+64880)
        assert (magic,version)==(0x31544c46,1) and flat in (0,1)
        row=dict(ns=time.monotonic_ns(),generation=header[3],flat=flat,switches=switches,
                 sha256=hashlib.sha256(packet[32:]).hexdigest())
        if latest is None or row['generation']!=latest['generation']:
            frames.append(row)
        latest=row
    async def send(op,**data):
        nonlocal seq
        if mode=='http':
            await asyncio.to_thread(post,owner+'/'+op,token,dict(run_id=run_id,**data))
        else:
            seq+=1;sent[seq]=time.monotonic_ns()
            await control.send(json.dumps(dict(seq=seq,op=op,run_id=run_id,**data)))
    async def receive_input():
        async for raw in control:
            msg=json.loads(raw)
            assert msg['type']=='ack' and 'error' not in msg,msg
            acks.append(dict(seq=msg['seq'],ms=(time.monotonic_ns()-sent.pop(msg['seq']))/1e6))
    async def receive_frames():
        if mode=='stream':
            while True:
                meta=json.loads(await video.recv())
                assert meta['state']['run_id']==run_id
                packet=await video.recv();observe(packet)
                assert meta['state']['frame'].endswith('-'+str(latest['generation']))
                await video.send(json.dumps(dict(frame=meta['state']['frame'])))
        else:
            last='';deadline=time.monotonic()
            while True:
                s=json.loads(await asyncio.to_thread(get,owner+'/status'))
                assert s['run_id']==run_id
                if s['frame'] and s['frame']!=last:
                    observe(await asyncio.to_thread(get,owner+'/frame.bin'))
                    last=s['frame']
                deadline=max(deadline+.05,time.monotonic())
                await asyncio.sleep(max(0,deadline-time.monotonic()))
    async def heartbeat():
        while True:
            await send('heartbeat');await asyncio.sleep(1)
    tasks=[]
    try:
        if mode=='stream':
            wsbase=gateway.replace('http://','ws://')
            control=await connect(wsbase+'/input',proxy=None,compression=None,max_size=131072)
            await control.send(json.dumps(dict(token=token)))
            assert json.loads(await control.recv())['type']=='ready'
            video=await connect(wsbase+'/video',proxy=None,compression=None,max_size=131072)
            await video.send(json.dumps(dict(token=token)))
            tasks.append(asyncio.create_task(receive_input()))
        tasks.extend([asyncio.create_task(receive_frames()),asyncio.create_task(heartbeat())])
        began=time.monotonic()
        while latest is None:
            for task in tasks:
                if task.done():await task
            assert time.monotonic()-began<10,'no frame'
            await asyncio.sleep(.01)
        initial=latest['flat']
        for i in range(trials):
            before=latest.copy();start=time.monotonic_ns()
            try:
                await send('key',key=192,down=1)
            finally:
                await send('key',key=192,down=0)
            deadline=time.monotonic()+10
            while latest['switches']!=before['switches']+1:
                for task in tasks:
                    if task.done():await task
                assert time.monotonic()<deadline,'F6 frame timeout'
                await asyncio.sleep(.002)
            assert latest['flat']==1-before['flat']
            pulses.append(dict(trial=i+1,ms=(latest['ns']-start)/1e6,
                before_generation=before['generation'],confirmed_generation=latest['generation']))
            await asyncio.sleep(.4)
        assert latest['flat']==initial,'use an even trial count'
        await asyncio.sleep(1)
        values=[x['ms'] for x in pulses]
        intervals=[(b['ns']-a['ns'])/1e6 for a,b in zip(frames,frames[1:])]
        return dict(mode=mode,host=host,run_id=run_id,trials=pulses,frames=frames,input_acks=acks,
            median_ms=statistics.median(values),min_ms=min(values),max_ms=max(values),
            delivered_fps=(len(frames)-1)*1e9/(frames[-1]['ns']-frames[0]['ns']),
            delivered_interval_p95_ms=sorted(intervals)[int(.95*len(intervals))])
    finally:
        for task in tasks:task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
        if control:await control.close()
        if video:await video.close()


async def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host',default='127.0.0.1')
    p.add_argument('--trials',type=int,default=8)
    p.add_argument('--order',default='http,stream,stream,http')
    a=p.parse_args()
    assert a.trials>=2 and a.trials%2==0
    results=[]
    try:
        for mode in a.order.split(','):
            assert mode in ('http','stream')
            result=await trial(mode,a.host,a.trials)
            results.append(result)
            print(f'{mode}: {result["median_ms"]:.2f} ms median, {result["delivered_fps"]:.2f} delivered FPS',file=sys.stderr,flush=True)
    finally:
        print(json.dumps(results,indent=2))


if __name__=='__main__':asyncio.run(main())
