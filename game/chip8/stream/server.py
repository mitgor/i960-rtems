#!/usr/bin/env python3
"""Independent input/video channels. Native simulation or explicit card owner.

The gateway never accesses PCI or adopts resources. Its card owner must already
be running with a matching boot/PID control record and complete hardware audits.
"""
import argparse,asyncio,importlib.util,io,json,secrets,signal,sys,time
from collections import deque
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE.parent))
from native import Player
from oracle import Oracle
from codec import packet,validate_frame
from host import demo_rom
spec=importlib.util.spec_from_file_location('chip8_shared_gateway',ROOT/'game/doom/play/accele160/stream/gateway.py')
shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
from websockets.asyncio.server import serve
from urllib.error import HTTPError

class NativeOwner:
    def __init__(self,rom,hz=500):
        self.rom,self.hz=rom,hz;self.epoch=secrets.randbits(32) or 1
        self.run_id=0;self.generation=0;self.slots=[None,None];self.frame=None
        self.events=deque();self.held=set();self.key_deadline=0.;self.stopped=False
        self.restart()
    def restart(self):
        self.run_id+=1;self.events.clear();self.held.clear();self.frame=None;self.stopped=False
        self.player=Player(self.rom,self.hz,self.now());self.oracle=Oracle(self.rom,self.hz)
    def now(self):return int(time.monotonic()*1000)&0xffffffff
    def status(self):
        return dict(run_id=self.run_id,state='idle' if self.stopped else 'running',
            message='CHIP-8 on native host simulation' if not self.stopped else 'CHIP-8 stopped; Start new game',
            frame=f'{self.epoch}-{self.generation}' if self.frame else '',keyboard_fifo=True,
            keyboard_mode='fifo',flat_planes=None,backend='Native host simulation',binary=True)
    async def call(self,path,body=None):
        if path=='/status':return self.status()
        if path=='/frame.bin':
            if self.frame is None:raise HTTPError(path,503,'no frame',{},None)
            return self.frame
        if body.get('run_id')!=self.run_id:raise HTTPError(path,409,'stale run',{},None)
        if path=='/restart':
            if not self.stopped:raise HTTPError(path,409,'not idle',{},None)
            self.restart();return dict(ok=True)
        if path=='/heartbeat':self.key_deadline=time.monotonic()+3;return dict(ok=True)
        if path=='/stop':self.stopped=True;self.events.clear();self.held.clear();return dict(ok=True)
        if self.stopped:raise HTTPError(path,409,'idle',{},None)
        values=body.get('events') if path=='/keys' else [body['key']|(body['down']<<8)]
        if not isinstance(values,list) or not 1<=len(values)<=16 or any(type(e) is not int or not 0<=e<=511 or (e&255)>15 for e in values):
            raise ValueError('key batch')
        held=set(self.held);events=[]
        for event in values:
            key=event&255;down=event>>8
            if down and key not in held:held.add(key);events.append(event)
            elif not down and key in held:held.remove(key);events.append(event)
        if len(self.events)+len(events)>16:
            self.stopped=True;self.events.clear();self.held.clear()
            raise HTTPError(path,429,'bounded input full; stopped',{},None)
        self.oracle.submit(events)
        self.held=held;self.events.extend(events);self.key_deadline=time.monotonic()+3
        return dict(ok=True)
    async def run(self):
        while True:
            if not self.stopped:
                if self.held and time.monotonic()>self.key_deadline:
                    # Release edges remain ordered and bounded. A full queue
                    # fails closed rather than dropping/overwriting accepted input.
                    if len(self.events)+len(self.held)>16:
                        self.stopped=True;self.events.clear();self.held.clear()
                    else:
                        self.oracle.submit(sorted(self.held))
                        self.events.extend(sorted(self.held));self.held.clear()
                if not self.stopped:
                    for _ in range(min(16,len(self.events))):self.player.key(self.events.popleft())
                    raw=self.player.update(self.now())
                    if raw is not None:
                        self.oracle.check(raw)
                        self.generation+=1
                        if self.generation>=0xfffffffe:raise RuntimeError('transport generation exhausted')
                        self.slots[(self.generation-1)&1]=packet(raw,self.epoch,self.generation)
                        self.frame=self.slots[(self.generation-1)&1]
            await asyncio.sleep(.01)

async def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--backend',choices=('native','card'),default='native')
    p.add_argument('--bind',default='127.0.0.1');p.add_argument('--port',type=int,default=8096)
    p.add_argument('--rom',type=Path);p.add_argument('--cpu-hz',type=int,default=500)
    p.add_argument('--control',type=Path,default=Path('/run/i960-chip8-control.json'));p.add_argument('--journal',type=Path)
    a=p.parse_args()
    if not 1024<=a.port<=65535 or not 1<=a.cpu_hz<=4000:p.error('port/CPU rate')
    if a.backend=='card' and (a.rom or a.cpu_hz!=500):p.error('card ROM/rate belong to the pinned card build')
    rom=a.rom.read_bytes() if a.rom else demo_rom()
    if not 2<=len(rom)<=3584:p.error('ROM length')
    owner=NativeOwner(rom,a.cpu_hz) if a.backend=='native' else shared.Owner(a.control)
    log=a.journal.open('a',buffering=1) if a.journal else io.StringIO()
    g=shared.Gateway(owner,log,allowed=range(16),frame_validator=validate_frame,page=HERE/'index.html',
        running_prefix='CHIP-8 on',reload_message='Restarting CHIP-8; RTEMS stays owned…')
    tasks=[];stop=asyncio.Event();loop=asyncio.get_running_loop()
    for sig in (signal.SIGINT,signal.SIGTERM):loop.add_signal_handler(sig,stop.set)
    try:
        async with serve(g.handler,a.bind,a.port,process_request=g.http,max_size=1024,max_queue=16,compression=None,close_timeout=.5):
            if isinstance(owner,NativeOwner):tasks.append(asyncio.create_task(owner.run()))
            tasks.append(asyncio.create_task(g.poll()));tasks.append(asyncio.create_task(stop.wait()))
            tasks.append(asyncio.create_task(g.closed.wait()))
            print(f'CHIP-8 {a.backend}: http://{a.bind}:{a.port}/',flush=True)
            done,_=await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                if not task.cancelled() and task.exception():raise task.exception()
    finally:
        g.closed.set()
        for task in tasks:task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True);log.close()
if __name__=='__main__':asyncio.run(main())
