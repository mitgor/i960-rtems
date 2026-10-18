#!/usr/bin/env python3
"""Same-kernel FIFO/mailbox/mailbox/FIFO comparison through persistent input.

Every mode starts from a freshly admitted game, with all owner audits intact.
The first FIFO game ends with a published full ring + STOP and the next fresh
game must explicitly account for that pending old-run input as discarded.
"""
import argparse
import asyncio
import json
from pathlib import Path
import re
import struct
import sys
import time
import urllib.request
from benchmark import trial


async def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host',default='127.0.0.1')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--order',default='fifo,mailbox,mailbox,fifo')
    p.add_argument('--single-only',action='store_true',help='32 phase-varied single presses per game; no pending STOP probe')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    base=f'http://{a.host}:8087'
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def request(path, body=None, token=None):
        req=urllib.request.Request(base+path,None if body is None else json.dumps(body).encode(),
            headers={'Content-Type':'application/json','X-Session-Token':token or ''})
        with opener.open(req,timeout=5) as r:return r.read()
    token=re.search(r"const token='([^']+)'",(await asyncio.to_thread(request,'/')).decode())[1]
    async def status():return json.loads(await asyncio.to_thread(request,'/status'))
    async def post(path,state,**body):
        return await asyncio.to_thread(request,path,dict(run_id=state['run_id'],**body),token)
    async def wait_idle():
        deadline=time.monotonic()+35
        while True:
            s=await status()
            if s['state']=='idle':return s
            assert time.monotonic()<deadline,'bounded idle timeout'
            await asyncio.sleep(.1)
    results=[];previous=None;probe_done=False
    for index,mode in enumerate(a.order.split(',')):
        assert mode in ('mailbox','fifo')
        s=await status();assert s['keyboard_fifo']
        if s['state']=='running' and (index or s['keyboard_mode']!=mode):
            await post('/stop',s);s=await wait_idle()
        if s['state']=='idle':
            await post('/keyboard-mode',s,mode=mode)
            await post('/restart',s)
        deadline=time.monotonic()+300
        while True:
            s=await status()
            if s['state']=='running' and s['keyboard_mode']==mode and s['message'].startswith('Doom on AcceleRAID'):
                packet=await asyncio.to_thread(request,'/frame.bin')
                if struct.unpack_from('<I',packet,32+64768+8)[0]>=40:break
            assert time.monotonic()<deadline,'fresh image/WAD/frame timeout'
            await asyncio.sleep(.5)
        assert s['flat_planes']==0 and s['flat_switches']==0,'fresh game must not inherit old input'
        if previous:
            assert s['keyboard_stats']['discarded']-previous['keyboard_stats']['discarded']==previous['keyboard_stats']['pending'],'old-run discard conservation'
        row=dict(index=index,mode=mode,run_id=s['run_id'],initial=s,probes=[],single_only=a.single_only)
        for burst,count in (((1,32),) if a.single_only else ((1,8),(2,8),(8,6))):
            result=await trial('stream',a.host,count,burst,jitter=a.single_only)
            assert result['keyboard_mode']==mode and result['run_id']==s['run_id']
            row['probes'].append(result)
            (a.out/f'{index}-{mode}.json').write_text(json.dumps(row,indent=2)+'\n')
            print(f'{index} {mode} burst={burst}: {result["median_ms"]:.2f} ms; {result["delivered_fps"]:.2f} delivered FPS',file=sys.stderr,flush=True)
        # Wait for the final key-up too, not merely the last visible mode change.
        deadline=time.monotonic()+5
        while True:
            s=await status();k=s['keyboard_stats']
            if k['published']==k['acked']:break
            assert time.monotonic()<deadline,'keyboard drain timeout'
            await asyncio.sleep(.02)
        if mode=='fifo' and not probe_done and not a.single_only:
            await post('/keys-stop',s,events=[448,192]*8)
            probe_done=True
        else:
            await post('/stop',s)
        final=await wait_idle()
        if mode=='fifo' and index==0 and not a.single_only:
            assert final['keyboard_stats']['pending']>0 and final['keyboard_stats']['max_depth']==16,'full ring STOP probe'
        row['final']=final;previous=final
        (a.out/f'{index}-{mode}.json').write_text(json.dumps(row,indent=2)+'\n')
        results.append(row)
        (a.out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(dict(games=len(results),final=previous),indent=2))


if __name__=='__main__':asyncio.run(main())
