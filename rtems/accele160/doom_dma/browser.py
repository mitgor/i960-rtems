#!/usr/bin/env python3
"""HTTP side of the AcceleRAID Doom owner; this module never touches PCI."""
import json,secrets,struct,threading,time
from collections import deque
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

ALLOWED={196,192,173,175,172,174,163,162,182,13,27,9,121,110,*range(49,56)}
class BrowserSession:
    def __init__(self,port=8087,runtime_flat=False,keyboard_mode='mailbox',keyboard_fifo=False,keyboard_test=False):
        assert keyboard_mode in ('mailbox','fifo') and (keyboard_mode=='mailbox' or keyboard_fifo)
        self.token=secrets.token_hex(24)
        self.epoch=secrets.randbits(32) or 1
        self.lock=threading.Lock()
        self.frame=None
        self.generation=0
        self.message='Loading Doom on the card…'
        self.events=deque()
        self.held=set()
        self.key_deadline=0.0
        self.stop=threading.Event()
        self.restart=threading.Event()
        self.run_id=1
        self.state="running"
        self.runtime_flat=runtime_flat
        self.keyboard_fifo=keyboard_fifo
        self.keyboard_mode=self.next_keyboard_mode=keyboard_mode
        self.keyboard_test=keyboard_test
        self.keyboard_stop_after_batch=threading.Event()
        self.keyboard_stats=None
        self.flat_mode=0
        self.flat_switches=0
        self.client_seen=0.0
        self.page=Path(__file__).with_name('index.html').read_text().replace(
            '__TOKEN__',self.token).encode()
        if not runtime_flat:
            self.page=self.page.replace(b'<button id="flat">Toggle flat planes (F6)</button> ',b'').replace(b'F6:192,',b'')
        owner=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def reply(self,code,body,kind='application/json'):
                self.send_response(code)
                self.send_header('Content-Type',kind)
                self.send_header('Cache-Control','no-store')
                self.send_header('Content-Length',str(len(body)))
                self.end_headers()
                try:self.wfile.write(body)
                except (BrokenPipeError,ConnectionResetError):pass
            def do_GET(self):
                if self.path=='/':return self.reply(200,owner.page,'text/html; charset=utf-8')
                if self.path=='/status':
                    with owner.lock:
                        state=dict(message=owner.message,
                                   frame=f'{owner.epoch}-{owner.generation}' if owner.frame else '',
                                   binary=True,stopped=owner.stop.is_set(),run_id=owner.run_id,state=owner.state,flat_planes=owner.flat_mode if owner.runtime_flat else None,flat_switches=owner.flat_switches,
                                   keyboard_mode=owner.keyboard_mode,next_keyboard_mode=owner.next_keyboard_mode,keyboard_fifo=owner.keyboard_fifo,keyboard_stats=owner.keyboard_stats)
                    return self.reply(200,json.dumps(state).encode())
                if self.path.startswith('/frame.bin'):
                    with owner.lock:packet=owner.frame
                    return self.reply(200,packet,'application/octet-stream') if packet else self.reply(503,b'no frame yet')
                self.reply(404,b'not found')
            def do_POST(self):
                if self.headers.get('X-Session-Token')!=owner.token or self.headers.get('Origin') not in (None,'http://'+self.headers.get('Host','')):
                    return self.reply(403,b'forbidden')
                try:
                    n=int(self.headers.get('Content-Length','0'))
                    if not 0<n<=256:raise ValueError('length')
                    body=json.loads(self.rfile.read(n))
                    if not isinstance(body,dict):raise ValueError("object required")
                    with owner.lock:
                        owner.client_seen=time.monotonic()
                        if self.path in ('/stop','/restart','/key','/keys','/keys-stop','/keyboard-mode'):
                            if type(body.get('run_id')) is not int or body['run_id']!=owner.run_id:
                                return self.reply(409,b'stale game')
                            if self.path in ('/restart','/keyboard-mode'):
                                if owner.state!='idle':return self.reply(409,b'game is not idle')
                            elif owner.state!='running':return self.reply(409,b'game is not running')
                        if self.path=='/keyboard-mode':
                            mode=body.get('mode')
                            if mode not in ('mailbox','fifo') or (mode=='fifo' and not owner.keyboard_fifo):raise ValueError('keyboard mode')
                            owner.next_keyboard_mode=mode
                        elif self.path=='/restart':owner.restart.set()
                        elif self.path in ('/keys','/keys-stop'):
                            values=body.get('events')
                            if not owner.keyboard_fifo or not isinstance(values,list) or not 1<=len(values)<=16:raise ValueError('key batch')
                            if self.path=='/keys-stop' and (not owner.keyboard_test or owner.keyboard_mode!='fifo' or len(values)!=16 or owner.events or owner.held):
                                return self.reply(409,b'keyboard STOP probe not ready/enabled')
                            held=set(owner.held);events=[]
                            for event in values:
                                if type(event) is not int or not 0<=event<=511:raise ValueError('key event')
                                key=event&255;down=event>>8
                                if key not in ALLOWED or (key==192 and not owner.runtime_flat):raise ValueError('key')
                                if down and key not in held:held.add(key);events.append(event)
                                elif not down and key in held:held.remove(key);events.append(event)
                            if len(owner.events)+len(events)>96:
                                owner.stop.set();return self.reply(429,b'key queue full')
                            if self.path=='/keys-stop' and (len(events)!=16 or held):raise ValueError('STOP probe needs sixteen balanced transitions')
                            owner.held=held;owner.events.extend(events);owner.key_deadline=time.monotonic()+3
                            if self.path=='/keys-stop':owner.keyboard_stop_after_batch.set()
                        elif self.path=='/stop':owner.stop.set()
                        elif self.path=='/heartbeat':owner.key_deadline=time.monotonic()+3
                        elif self.path=='/key':
                            key=body['key'];down=body['down']
                            if type(key) is not int or key not in ALLOWED or (key==192 and not owner.runtime_flat) or type(down) is not int or down not in (0,1):raise ValueError('key')
                            if len(owner.events)>=96:
                                owner.stop.set();return self.reply(429,b'key queue full')
                            if down and key not in owner.held:owner.held.add(key);owner.events.append(key|0x100)
                            elif not down and key in owner.held:owner.held.remove(key);owner.events.append(key)
                            owner.key_deadline=time.monotonic()+3
                        else:return self.reply(404,b'not found')
                    self.reply(200,b'{}')
                except (ValueError,KeyError,TypeError):self.reply(400,b'invalid request')
        self.http=ThreadingHTTPServer(('0.0.0.0',port),Handler)
        self.port=self.http.server_port
        self.thread=threading.Thread(target=self.http.serve_forever,daemon=True)
        self.thread.start()
    def begin_game(self,run_id):
        with self.lock:
            assert run_id>=self.run_id
            self.run_id=run_id;self.state='running';self.flat_mode=0;self.flat_switches=0
            self.keyboard_mode=self.next_keyboard_mode
            self.events.clear();self.held.clear();self.stop.clear();self.restart.clear()
            self.keyboard_stop_after_batch.clear();self.keyboard_stats=None
            self.message=f'Loading game {run_id} on the card…'
            return self.keyboard_mode
    def idle(self,run_id):
        with self.lock:
            assert run_id==self.run_id
            self.state='idle';self.events.clear();self.held.clear();self.restart.clear()
            self.message=f'Game {run_id} stopped safely. Click Start new game.'
    def publish(self,generation,payload,profile=None):
        assert len(payload)==65536 and 0<generation<=0xffffffff
        packet=struct.pack('<8I',0x31424644,1,self.epoch,generation,320,200,65536,0)+payload
        with self.lock:
            assert generation>self.generation
            if self.runtime_flat:
                assert profile is not None and profile['flat_planes'] in (0,1)
                self.flat_mode=profile['flat_planes'];self.flat_switches=profile['flat_switches']
            self.frame=packet
            self.generation=generation
            self.message=f'Doom on AcceleRAID 160 · frame {generation}'
    def next_key(self):
        with self.lock:
            if self.held and time.monotonic()>self.key_deadline:
                for key in sorted(self.held):self.events.append(key)
                self.held.clear()
            return self.events.popleft() if self.events else None
    def disconnected(self,seconds):
        with self.lock:
            return bool(self.client_seen and time.monotonic()-self.client_seen>seconds)
    def close(self,message='Session ended'):
        with self.lock:self.message=message
        self.http.shutdown();self.http.server_close();self.thread.join(timeout=3)
