"""Independent wire-format and archived hardware response verification."""
import json
from pathlib import Path
import struct
import unittest
import buffer_io as bio
from loadrun import verify
ROOT=Path(__file__).resolve().parents[2]

class BufferTests(unittest.TestCase):
    def fixture(self):
        image=bio.prepare(b'\0'*4,b'abc',bio.OUTPUT_MAX,17).ljust(524288,b'\0')
        after=bytearray(image)
        struct.pack_into('<3I',after,bio.OFFSET+20,0,3,17)
        after[bio.OFFSET+bio.OUTPUT:bio.OFFSET+bio.OUTPUT+3]=b'ABC'
        return image,after
    def test_bounds(self):
        for code,data,cap,seq,entry in [(b'',b'',0,1,0),(b'123',b'',0,1,0),(b'0'*32772,b'',0,1,0),(b'1234',b'0'*4097,0,1,0),(b'1234',b'',8193,1,0),(b'1234',b'',1,0,0),(b'1234',b'',1,1,4)]:
            with self.assertRaises(ValueError):bio.prepare(code,data,cap,seq,entry)
        self.assertEqual(len(bio.prepare(bytes(32768),bytes(4096),8192,0xffffffff,32764)),bio.IMAGE_SIZE)
    def test_corrupt_responses(self):
        before,after=self.fixture()
        self.assertEqual(bio.response(before,after),(0,b'ABC'))
        for pos,val in [(bio.OFFSET+24,8193),(bio.OFFSET+28,16),(bio.OFFSET+20,bio.PENDING),(bio.OFFSET+20,2),(bio.OFFSET+4,2)]:
            bad=bytearray(after);struct.pack_into('<I',bad,pos,val)
            with self.assertRaises(ValueError):bio.response(before,bad)
        for pos in [0,bio.OFFSET+32,bio.OFFSET+64,bio.OFFSET+bio.GUARD1,bio.OFFSET+bio.GUARD2,bio.OFFSET+bio.OUTPUT+3,524287]:
            bad=bytearray(after);bad[pos]^=1
            with self.assertRaises(ValueError):bio.response(before,bad)
        with self.assertRaises(ValueError):bio.response(before,after[:-1])
    def test_maximum_and_error_response(self):
        before,after=self.fixture()
        struct.pack_into('<3I',after,bio.OFFSET+20,0,8192,17)
        after[bio.OFFSET+bio.OUTPUT:bio.OFFSET+bio.GUARD2]=bytes(range(256))*32
        self.assertEqual(len(bio.response(before,after)[1]),8192)
        after=bytearray(before);struct.pack_into('<3I',after,bio.OFFSET+20,2,0,17)
        self.assertEqual(bio.response(before,after),(2,b''))
    def test_live_captures(self):
        base=ROOT/'artifacts/buffer-io-20261010'
        frame=bytes(ord('#') if r in (0,23) or c in (0,79) else ord('A')+(r+c)%26 for r in range(24) for c in range(80))
        cases=[('run-text',b'Hello from the real i960!\n'+bytes(x^32 for x in b'abcXYZ012\n'),0),
               ('run-frame',frame,0),('run-repeat',b'Hello from the real i960!\n'+bytes(x^32 for x in b'Second call'),0),
               ('run-small-capacity',b'',2)]
        for name,expected,status in cases:
            p=base/name
            self.assertEqual(verify(p,(p/'payload.bin').read_bytes()),0)
            self.assertEqual((p/'response.bin').read_bytes(),expected)
            self.assertEqual(json.loads((p/'response.json').read_text())['status'],status)
        p=base/'run-legacy'
        self.assertEqual(verify(p,(p/'payload.bin').read_bytes()),6765)

if __name__=='__main__': unittest.main()
