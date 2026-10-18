#!/usr/bin/env python3
"""Browser transport only: no PCI access, card resource adoption or audit bypass.

Two independent WebSockets: ordered input and a two-credit latest-frame stream.
Upstream is the existing audited owner, on loopback. Never synthesize heartbeats
without a real control client. Owner identity is pinned for this process lifetime.
"""
import argparse
import asyncio
from collections import deque
import hashlib
import json
import os
from pathlib import Path
import secrets
import signal
import struct
import time
import urllib.request
import urllib.error

from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

ALLOWED = {196,192,173,175,172,174,163,162,182,13,27,9,121,110,*range(49,56)}


def validate_frame(packet):
    if len(packet) != 65568:
        raise ValueError('frame length')
    magic, version, epoch, generation, width, height, size, reserved = struct.unpack_from('<8I', packet)
    if (magic, version, width, height, size, reserved) != (0x31424644,1,320,200,65536,0) or not epoch or not generation:
        raise ValueError('frame header')
    return epoch, generation


class Owner:
    def __init__(self, control):
        self.path = control
        self.identity = json.loads(control.read_text())
        self.base = 'http://127.0.0.1:' + str(self.identity['port'])
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def check(self):
        if json.loads(self.path.read_text()) != self.identity:
            raise RuntimeError('owner changed; restart gateway explicitly')
        if Path('/proc/sys/kernel/random/boot_id').read_text().strip() != self.identity['boot_id']:
            raise RuntimeError('owner boot changed')
        os.kill(self.identity['pid'], 0)

    def request(self, path, body=None):
        self.check()
        request = urllib.request.Request(self.base + path,
            None if body is None else json.dumps(body).encode(),
            headers={'Content-Type':'application/json', 'X-Session-Token':self.identity['token']})
        with self.opener.open(request, timeout=2) as response:
            data = response.read(65569)
        return data if path == '/frame.bin' else json.loads(data)

    async def call(self, path, body=None):
        return await asyncio.to_thread(self.request, path, body)


class Gateway:
    def __init__(self, owner, journal):
        self.owner = owner
        self.token = secrets.token_hex(24)
        self.journal = journal
        self.controller = None
        self.videos = 0
        self.latest = None
        self.status = None
        self.restart_pending = None
        self.closed = asyncio.Event()

    def display_state(self, state):
        if state['run_id'] == self.restart_pending and state['state'] == 'idle':
            return dict(state,state='reloading',message='Reloading Doom image and WAD; RTEMS stays owned…')
        return state

    def record(self, **data):
        self.journal.write(json.dumps(dict(host_ns=time.monotonic_ns(), **data)) + '\n')
        self.journal.flush()

    async def poll(self):
        while not self.closed.is_set():
            try:
                state = await self.owner.call('/status')
                if self.status and state['run_id'] != self.status['run_id']:
                    self.latest = None
                if self.restart_pending is not None and state['run_id'] != self.restart_pending:
                    self.restart_pending = None
                self.status = self.display_state(state)
                if not self.videos:
                    self.latest = None
                # Do not relabel a retained previous game's frame as a new one.
                if self.videos and state['frame'] and state['message'].startswith('Doom on AcceleRAID'):
                    if self.latest is None or state['frame'] != self.latest[0]['frame']:
                        packet = await self.owner.call('/frame.bin')
                        epoch, generation = validate_frame(packet)
                        if state['frame'] != f'{epoch}-{generation}':
                            await asyncio.sleep(.002)
                            continue  # Racing publication: retry rather than mislabel mode/run.
                        meta = dict(state, frame=f'{epoch}-{generation}')
                        self.latest = (meta, packet)
                await asyncio.sleep(.01)
            except Exception as error:
                self.record(type='upstream_failure', error=type(error).__name__)
                self.closed.set()  # Never reconnect to or adopt a replacement owner.

    async def http(self, connection, request):
        origin = request.headers.get('Origin')
        if origin not in (None, 'http://' + request.headers.get('Host','')):
            return connection.respond(403, 'origin rejected\n')
        if request.path in ('/input','/video'):
            return None
        if request.path == '/':
            page = Path(__file__).with_name('index.html').read_text().replace('__TOKEN__',self.token)
            response = connection.respond(200, page)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
        elif request.path == '/status':
            response = connection.respond(200, json.dumps(self.status))
            response.headers['Content-Type'] = 'application/json'
        else:
            return connection.respond(404, 'not found\n')
        response.headers['Cache-Control'] = 'no-store'
        return response

    async def handler(self, ws):
        try:
            auth = json.loads(await asyncio.wait_for(ws.recv(), 3))
            if not isinstance(auth, dict):
                raise ValueError('authentication object')
            if not secrets.compare_digest(str(auth.get('token','')), self.token):
                return await ws.close(1008, 'authentication')
            if ws.request.path == '/input':
                if self.controller is not None:
                    return await ws.close(1008, 'controller already attached')
                self.controller = ws
                await self.control(ws)
            elif ws.request.path == '/video':
                if self.videos >= 4:
                    return await ws.close(1008, 'viewer limit')
                self.videos += 1
                try:
                    await self.video(ws)
                finally:
                    self.videos -= 1
                    if not self.videos:
                        self.latest = None  # A reconnect must wait for a fresh upstream snapshot.
        except (ConnectionClosed, asyncio.TimeoutError, ValueError, KeyError, TypeError):
            await ws.close(1008, 'invalid or timed out message')
        except (OSError, RuntimeError):
            self.record(type='owner_lost')
            self.closed.set()
            await ws.close(1011, 'owner unavailable')

    async def control(self, ws):
        seq = 0
        held = set()
        held_run = None
        try:
            await ws.send(json.dumps(dict(type='ready', state=self.display_state(await self.owner.call('/status')))))
            while True:
                message = json.loads(await asyncio.wait_for(ws.recv(), 3))
                if not isinstance(message, dict):
                    raise ValueError('input object')
                began = time.monotonic_ns()
                if type(message.get('seq')) is not int or message['seq'] != seq + 1:
                    raise ValueError('input sequence')
                seq += 1
                state = await self.owner.call('/status')
                if held_run != state['run_id']:
                    held.clear()
                    held_run = state['run_id']
                op = message.get('op')
                if type(message.get('run_id')) is not int or message['run_id'] != state['run_id']:
                    await ws.send(json.dumps(dict(type='ack',seq=seq,error='stale game',state=state)))
                    continue
                body = dict(run_id=state['run_id'])
                if op == 'key':
                    key, down = message.get('key'), message.get('down')
                    if type(key) is not int or key not in ALLOWED or type(down) is not int or down not in (0,1):
                        raise ValueError('key')
                    if state['state'] != 'running':
                        await ws.send(json.dumps(dict(type='ack',seq=seq,error='game idle',state=state)))
                        continue
                    body.update(key=key, down=down)
                elif op not in ('heartbeat','stop','restart'):
                    raise ValueError('operation')
                if op == 'restart' and self.restart_pending == state['run_id']:
                    await ws.send(json.dumps(dict(type='ack',seq=seq,error='reload already requested',state=self.display_state(state))))
                    continue
                try:
                    await self.owner.call('/' + op, body)
                except urllib.error.HTTPError as error:
                    await ws.send(json.dumps(dict(type='ack',seq=seq,error=str(error.code),state=state)))
                    continue
                if op == 'key':
                    if down: held.add(key)
                    else: held.discard(key)
                if op == 'restart':
                    self.restart_pending = state['run_id']
                self.record(type='input', seq=seq, op=op, run_id=state['run_id'],
                    forward_ms=(time.monotonic_ns()-began)/1e6)
                await ws.send(json.dumps(dict(type='ack',seq=seq,state=self.display_state(state))))
        finally:
            # A broken connection must not leave accepted keys held. The owner's
            # independent 3 s key deadline also covers gateway/process death.
            try:
                state = await self.owner.call('/status')
                if state['run_id'] == held_run and state['state'] == 'running':
                    for key in sorted(held):
                        await self.owner.call('/key',dict(run_id=held_run,key=key,down=0))
                self.record(type='control_disconnected', released=len(held))
            except (OSError, RuntimeError):
                self.record(type='disconnect_owner_unavailable')
                self.closed.set()
            finally:
                self.controller = None

    async def video(self, ws):
        pending = deque()
        last = None
        async def acknowledgements():
            async for raw in ws:
                message = json.loads(raw)
                if not pending or message != dict(frame=pending[0][0]):
                    raise ValueError('video ACK identity/order')
                frame, began = pending.popleft()
                self.record(type='display_ack',frame=frame,elapsed_ms=(time.monotonic_ns()-began)/1e6)
        reader = asyncio.create_task(acknowledgements())
        try:
            while not self.closed.is_set():
                if reader.done():
                    await reader
                    return
                if pending and time.monotonic_ns()-pending[0][1] > 5_000_000_000:
                    return await ws.close(1008,'display stalled')
                current = self.latest
                if current and current[0]['frame'] != last and len(pending) < 2:
                    meta, packet = current
                    last = meta['frame']
                    began = time.monotonic_ns()
                    pending.append((last,began))
                    await asyncio.wait_for(ws.send(json.dumps(dict(type='frame',state=meta))), 2)
                    await asyncio.wait_for(ws.send(packet), 2)
                    self.record(type='frame',frame=last,run_id=meta['run_id'],
                        sha256=hashlib.sha256(packet[32:]).hexdigest(),inflight=len(pending))
                await asyncio.sleep(.002)
        finally:
            reader.cancel()
            await asyncio.gather(reader, return_exceptions=True)


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8088)
    parser.add_argument('--control',type=Path,default=Path('/run/i960-doom-control.json'))
    parser.add_argument('--journal',type=Path,required=True)
    args = parser.parse_args()
    with args.journal.open('a', buffering=1) as journal:
        owner = Owner(args.control)
        owner.check()
        gateway = Gateway(owner,journal)
        for sig in (signal.SIGTERM,signal.SIGINT):
            asyncio.get_running_loop().add_signal_handler(sig,gateway.closed.set)
        async with serve(gateway.handler,'0.0.0.0',args.port,
            process_request=gateway.http,max_size=1024,max_queue=16,
            write_limit=65536,compression=None,close_timeout=1,ping_interval=10,ping_timeout=5):
            poll = asyncio.create_task(gateway.poll())
            print(f'Doom stream on port {args.port}; existing audited owner only',flush=True)
            await gateway.closed.wait()
            poll.cancel()
            await asyncio.gather(poll,return_exceptions=True)


if __name__ == '__main__':
    asyncio.run(main())
