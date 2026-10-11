#!/usr/bin/env python3
"""Loopback browser framebuffer bridge. Default backend is explicitly native."""
import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import TCPServer
from host import HERE, Native, card_backend, decode, demo_rom, request


class FailClosedServer(HTTPServer):
    def server_bind(self):
        # HTTPServer's reverse DNS lookup can stall startup on offline hosts.
        TCPServer.server_bind(self)
        self.server_name = 'localhost'
        self.server_port = self.server_address[1]

    def handle_error(self, request, client_address):
        # Propagate backend errors to main's finally, which performs the audited
        # session close. Never continue issuing requests after a transport fault.
        raise


class Game:
    def __init__(self, backend, rom, label):
        self.backend, self.rom, self.label = backend, rom, label
        self.last = time.monotonic()
        self.tick_fraction = self.cycle_fraction = 0.0
        self.reply = decode(backend.step(request(op=0, seed=1, rom=rom)))

    def update(self, keys, reset=False, now=None):
        now = time.monotonic() if now is None else now
        if reset:
            data = request(op=0, seed=1, rom=self.rom)
            self.tick_fraction = self.cycle_fraction = 0.0
        else:
            # Bound work after a suspended browser. No unbounded catch-up loop.
            elapsed = min(0.25, max(0, now - self.last))
            self.tick_fraction += elapsed * 60
            self.cycle_fraction += elapsed * 500
            ticks, cycles = int(self.tick_fraction), int(self.cycle_fraction)
            self.tick_fraction -= ticks
            self.cycle_fraction -= cycles
            data = request(cycles=cycles, keys=keys, ticks=ticks)
        self.last = now
        self.reply = decode(self.backend.step(data))
        return dict(self.reply, backend=self.label)


def handler(game):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def send(self, code, content, mime):
            self.send_response(code)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self):
            if self.path == '/':
                self.send(200, (HERE / 'web/index.html').read_bytes(), 'text/html; charset=utf-8')
            else:
                self.send(404, b'Not found', 'text/plain')

        def do_POST(self):
            if self.path != '/step':
                self.send(404, b'Not found', 'text/plain')
                return
            # Same-origin browser client only; do not accept cross-site forms.
            origin = self.headers.get('Origin')
            if origin and origin != 'http://' + self.headers.get('Host', ''):
                self.send(403, b'Wrong origin', 'text/plain')
                return
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 128 or self.headers.get_content_type() != 'application/json':
                    raise ValueError('invalid body')
                data = json.loads(self.rfile.read(size))
                keys = data.get('keys', 0)
                reset = data.get('reset', False)
                if type(keys) is not int or not 0 <= keys <= 65535 or type(reset) is not bool:
                    raise ValueError('invalid controls')
            except (ValueError, TypeError, AttributeError):
                self.send(400, b'Invalid controls', 'text/plain')
                return
            result = game.update(keys, reset)
            self.send(200, json.dumps(result).encode(), 'application/json')

        def log_message(self, *_):
            pass
    return Handler


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--backend', choices=['native', 'card'], default='native')
    p.add_argument('--port', type=int, default=8096)
    p.add_argument('--rom', type=Path)
    p.add_argument('--payload', type=Path)
    p.add_argument('--module', type=Path)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    rom = a.rom.read_bytes() if a.rom else demo_rom()
    if not 2 <= len(rom) <= 3584:
        p.error('ROM must contain 2..3584 bytes')
    if a.backend == 'card' and not all([a.payload, a.module, a.output]):
        p.error('card requires --payload, --module and a fresh --output directory')
    # Bind before acquiring hardware, so a port conflict cannot strand a session.
    server = FailClosedServer(('127.0.0.1', a.port), BaseHTTPRequestHandler)
    server.timeout = 5
    backend = None
    try:
        backend = Native() if a.backend == 'native' else card_backend(a.payload, a.module, a.output)
        game = Game(backend, rom, 'Native host simulation' if a.backend == 'native' else 'Mylex / RTEMS (bounded callbacks)')
        server.RequestHandlerClass = handler(game)
        print(f'{game.label}: http://127.0.0.1:{a.port}/', flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if backend is not None:
            backend.close()


if __name__ == '__main__':
    main()
