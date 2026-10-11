#!/usr/bin/env python3
import http.client
import json
import threading
import unittest
from host import Native, decode, demo_rom, request
from server import FailClosedServer, Game, handler


class ProtocolTests(unittest.TestCase):
    def test_demo_replay(self):
        a, b = Native(), Native()
        reset = request(op=0, seed=77, rom=demo_rom())
        self.assertEqual(a.step(reset), b.step(reset))
        frames = set()
        for i in range(1200):
            req = request(cycles=20, ticks=2, keys=1 << ([4, 6, 2, 8][i // 100 % 4]))
            reply = a.step(req)
            self.assertEqual(reply, b.step(req))
            state = decode(reply)
            self.assertEqual(state['status'], 0)
            frames.add(state['frame'])
        self.assertGreater(len(frames), 32)
        self.assertEqual(state['total'], 24000)

    def test_rejection_does_not_reset(self):
        a = Native()
        a.step(request(op=0, rom=demo_rom()))
        before = a.step(request(cycles=20))
        for req in [b'', request(op=2), request(cycles=1001),
                    request(keys=65536), request(ticks=61), request(seed=1),
                    request(op=0, rom=b'X' * 3585)]:
            with self.assertRaises(ValueError):
                a.step(req)
        # Only last-call executed changes when querying without advancing.
        self.assertEqual(a.step(request())[12:], before[12:])

    def test_bounded_elapsed_and_reset(self):
        game = Game(Native(), demo_rom(), 'test')
        before = game.last
        result = game.update(0, now=before + 1000)
        self.assertEqual(result['executed'], 125)
        self.assertEqual(game.update(0, reset=True)['total'], 0)

    def test_http(self):
        game = Game(Native(), demo_rom(), 'Native host simulation')
        server = FailClosedServer(('127.0.0.1', 0), handler(game))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            conn = http.client.HTTPConnection(*server.server_address, timeout=2)
            conn.request('GET', '/')
            response = conn.getresponse()
            self.assertEqual(response.status, 200)
            self.assertIn(b'<canvas', response.read())
            for body, code in [(dict(keys=16), 200), (dict(keys=-1), 400),
                               (dict(keys=True), 400), (dict(reset='yes'), 400)]:
                conn.request('POST', '/step', json.dumps(body), {'Content-Type': 'application/json'})
                response = conn.getresponse()
                self.assertEqual(response.status, code)
                data = response.read()
                if code == 200:
                    self.assertEqual(json.loads(data)['backend'], 'Native host simulation')
            conn.request('POST', '/step', '{}', {'Content-Type': 'application/json', 'Origin': 'http://unrelated.invalid'})
            response = conn.getresponse()
            self.assertEqual(response.status, 403)
            response.read()
            conn.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
