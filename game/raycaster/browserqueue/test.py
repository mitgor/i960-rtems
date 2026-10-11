#!/usr/bin/env python3
"""Host ownership, control/reset equivalence and fail-stop audit mutations."""
import gzip
import json
from pathlib import Path
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time
import unittest
GAME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GAME))
from browserqueue.backend import AuditedQueue, expected_commands
from combined.model import Model, base
from host import Native, request
from server import Game, FailClosedServer, handler

class FakeBoard:
    def __init__(self, out):
        self.debugfs = out / 'debug'
        self.debugfs.mkdir()
        self.sequence = self.closes = 0
        self.model = Model()
        self.fault = None
    def step(self, data):
        self.sequence += 1
        if self.fault == 'timeout':
            raise TimeoutError('uncertain completion')
        reply = self.model.step(data, self.sequence)
        snapshot = bytearray(524288)
        snapshot[base.OFFSET:base.OFFSET+2*base.SIZE] = b''.join(self.model.slots)
        files = {'payload-after': bytes(snapshot), 'frame-descriptor': reply}
        files.update({f'frame-slot{i}': s for i, s in enumerate(self.model.slots)})
        for name, content in files.items():
            for sentinel in ('a5', '5a'):
                if self.fault == name and sentinel == '5a':
                    content = bytes([content[0]^1]) + content[1:]
                (self.debugfs / f'{name}-{sentinel}.bin').write_bytes(content)
        commands = expected_commands(self.sequence, self.model.mask)
        if self.fault == 'commands':
            commands.pop()
        log = ''
        for op, count, offset in commands:
            log += f'submit op={op:x}\ncomplete op={op:x}\nCMDPROFILE op={op:x} count={count} offset={offset:x} gate=0 input=0 prepare=0 submit_log=0 submit=0 wait=0 consume=0 scan=0 complete_log=0 tail=0 total=0\n'
        log += f'RAYPROFILE seq={self.sequence} upload=1 arm=1 execute=1 verify=1 audit=2 total=6 bytes=524288\nFQPROFILE seq={self.sequence} mask={self.model.mask} targeted_ns=1 full_audit_ns=1\n'
        (self.debugfs / 'result.txt').write_text(log)
        return bytes(64) if self.fault == 'reply' else reply
    def close(self):
        self.closes += 1

class Tests(unittest.TestCase):
    def test_controls_reset_and_all_audits(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp); board = FakeBoard(out); backend = AuditedQueue(board, out, epoch=17)
            a, b = Game(backend, 'queue'), Game(Native(), 'native')
            for i in range(70):
                reset = i in (5, 6, 24, 69)
                x, y = a.update(i % 16, reset), b.update(i % 16, reset)
                for key in y.keys() - {'backend', 'callback_ms'}:
                    self.assertEqual(x[key], y[key], (i, key))
            backend.close(); backend.close()
            self.assertEqual(board.closes, 1)
            self.assertEqual(len(gzip.decompress((out/'full-audits.bin.gz').read_bytes())), board.sequence * 524288)
            self.assertEqual(backend.model.epoch, 21)
            self.assertEqual(len(backend.rows), board.sequence)
            self.assertEqual(len(json.loads((out/'browser-requests.json').read_text())), board.sequence)
    def test_faults_never_retry(self):
        for fault in ('timeout', 'reply', 'payload-after', 'frame-descriptor', 'frame-slot0', 'commands'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                out=Path(tmp); board=FakeBoard(out); backend=AuditedQueue(board,out,17)
                backend.step(request(op=0,columns=0)); backend.step(request())
                board.fault=fault
                with self.assertRaises((AssertionError,TimeoutError)):
                    backend.step(request(keys=8))
                sequence=board.sequence
                with self.assertRaises(RuntimeError):backend.step(request(keys=8))
                self.assertEqual(board.sequence,sequence)
                backend.close(); self.assertEqual(board.closes,1)
    def test_disconnect_after_execution_is_fatal(self):
        # A completed, validated frame followed by a failed socket write must
        # unwind the server, not re-execute the input or swallow the exception.
        import io
        game=Game(Native(),'native')
        cls=handler(game); obj=object.__new__(cls)
        obj.path='/step'; obj.headers=__import__('email').message.Message()
        obj.headers['Content-Type']='application/json'; obj.headers['Content-Length']='10'
        obj.rfile=io.BytesIO(b'{"keys":8}')
        def disconnected(*args):raise BrokenPipeError('client gone')
        obj.send=disconnected
        with self.assertRaises(BrokenPipeError):obj.do_POST()
        self.assertEqual(game.updates,1)
        self.assertEqual(game.reply['angle'],4)
        with self.assertRaises(BrokenPipeError):
            try:raise BrokenPipeError()
            except BrokenPipeError:FailClosedServer.handle_error(None,None,None)
    def test_signal_during_request_finishes_before_close(self):
        import http.client, threading
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp); marker=out/'executing'; closed=out/'closed'
            with socket.socket() as sock:
                sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
            code = f"""
import sys,time,struct
from pathlib import Path
sys.path.insert(0,{str(GAME)!r})
import server
Original=server.Native
class Slow(Original):
 def step(self,data):
  if struct.unpack_from('<I',data,4)[0]==1:
   Path({str(marker)!r}).write_text('executing')
   time.sleep(.3)
  return super().step(data)
 def close(self):Path({str(closed)!r}).write_text('closed')
server.Native=Slow
server.main()
"""
            capture=out/'capture'
            proc=subprocess.Popen([sys.executable,'-c',code,'--port',str(port),'--output',str(capture)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            results=[]
            def fetch():
                client=http.client.HTTPConnection('127.0.0.1',port,timeout=3)
                client.request('POST','/step','{"keys":8}',{'Content-Type':'application/json'})
                response=client.getresponse();results.append((response.status,json.loads(response.read())));client.close()
            try:
                self.assertIn('Native host simulation',proc.stdout.readline())
                thread=threading.Thread(target=fetch);thread.start()
                deadline=time.monotonic()+2
                while not marker.exists() and time.monotonic()<deadline:time.sleep(.005)
                self.assertTrue(marker.exists());proc.send_signal(signal.SIGTERM)
                thread.join(timeout=3);_,err=proc.communicate(timeout=3)
                self.assertEqual(proc.returncode,0,err);self.assertTrue(closed.exists())
                self.assertEqual(results[0][0],200);self.assertEqual(results[0][1]['angle'],4)
                self.assertEqual(json.loads((capture/'browser-session.json').read_text())['exit_reason'],'signal')
            finally:
                if proc.poll() is None:proc.kill();proc.wait()

    def test_idle_and_sigterm_exit(self):
        for term in (False, True):
            with socket.socket() as sock:
                sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
            proc=subprocess.Popen([sys.executable,str(GAME/'server.py'),'--port',str(port),'--idle-timeout','1'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                self.assertIn('Native host simulation',proc.stdout.readline())
                if term:proc.send_signal(signal.SIGTERM)
                _,err=proc.communicate(timeout=4)
                self.assertEqual(proc.returncode,0,err)
            finally:
                if proc.poll() is None:proc.kill();proc.wait()

if __name__=='__main__':unittest.main()
