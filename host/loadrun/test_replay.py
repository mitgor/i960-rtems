import json,tempfile,unittest
from pathlib import Path
from capture_archive import pack,read,unpack
from tetris_replay import next_request,stats
from tetris_wire import request

class ReplayTests(unittest.TestCase):
    def test_capture_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);src=d/'capture';src.mkdir();base=bytes(range(256))*2048
            (src/'image.bin').write_bytes(base[:100]+b'changed!'+base[108:])
            (src/'text.txt').write_bytes(b'hello\0\xff');(src/'empty.bin').write_bytes(b'')
            z=d/'run.zip';pack(src,z,base)
            unpack(z,d/'restored',base)
            self.assertEqual({p.name:p.read_bytes() for p in src.iterdir()},read(z,base))
            with self.assertRaises(ValueError):read(z,bytes(len(base)))
            with self.assertRaises(ValueError):pack(src,z,base)
    def test_deterministic_schedule(self):
        self.assertEqual(next_request(None,0),('init',request(seed=1)))
        state=bytearray(240)
        self.assertEqual(next_request(state,126),('quit',request(state,key=ord('q'),ticks=0)))
        self.assertEqual(next_request(state,250),('init',request(seed=251)))
        state[32]=1;self.assertEqual(next_request(state,2),('init',request(seed=3)))
        self.assertEqual(stats([1_000_000,3_000_000,2_000_000])['median_ms'],2)
if __name__=='__main__':unittest.main()
