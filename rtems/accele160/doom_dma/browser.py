#!/usr/bin/env python3
"""HTTP side of the AcceleRAID Doom owner; this module never touches PCI."""
import json,secrets,struct,threading,time
from collections import deque
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

ALLOWED={173,175,172,174,163,162,182,13,27,9,121,110,*range(49,56)}
class BrowserSession:
    def __init__(self,port=8087):
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
        self.client_seen=0.0
        self.page=Path(__file__).with_name('index.html').read_text().replace(
            '__TOKEN__',self.token).encode()
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
                                   binary=True,stopped=owner.stop.is_set())
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
                    if not 0<n<=128:raise ValueError('length')
                    body=json.loads(self.rfile.read(n))
                    with owner.lock:owner.client_seen=time.monotonic()
                    if self.path=='/stop':
                        owner.stop.set()
                    elif self.path=='/heartbeat':
                        with owner.lock:owner.key_deadline=time.monotonic()+3
                    elif self.path=='/key':
                        key=body['key'];down=body['down']
                        if type(key) is not int or key not in ALLOWED or type(down) is not int or down not in (0,1):raise ValueError('key')
                        with owner.lock:
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
    def publish(self,generation,payload):
        assert len(payload)==65536 and 0<generation<=0xffffffff
        packet=struct.pack('<8I',0x31424644,1,self.epoch,generation,320,200,65536,0)+payload
        with self.lock:
            assert generation>self.generation
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
