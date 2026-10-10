#!/usr/bin/env python3
import ctypes,random,struct,subprocess,tempfile,unittest
from pathlib import Path
import wire
class WireTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();p=Path(cls.tmp.name)
  (p/'check.c').write_text('#include "buffer_io.h"\nint check(const unsigned char*a,const unsigned char*b,unsigned int n){return bio_response_valid(a,b,n);}\n')
  lib=p/'check.so';subprocess.run(['cc','-shared','-fPIC','-I'+str(Path(__file__).parent),str(p/'check.c'),'-o',str(lib)],check=True)
  cls.lib=ctypes.CDLL(str(lib));cls.lib.check.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_uint];cls.lib.check.restype=ctypes.c_int
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def images(self):
  before=wire.prepare(b'\x01\x02\x03\x04')+bytes(524288-wire.bio.IMAGE_SIZE);after=bytearray(before)
  struct.pack_into('<3I',after,wire.bio.OFFSET+20,0,4,1);after[wire.bio.OFFSET+wire.bio.OUTPUT:wire.bio.OFFSET+wire.bio.OUTPUT+4]=b'test'
  return before,after
 def valid(self,b,a):return bool(self.lib.check(b,bytes(a),len(b)))
 def test_mutable_bounds_and_immutable_guards(self):
  b,a=self.images();self.assertTrue(self.valid(b,a));self.assertEqual(wire.response(b,a),(0,b'test'))
  for offset in [wire.MUTABLE_START,wire.MUTABLE_END-1,0x40000]:
   c=bytearray(a);c[offset]^=1;self.assertTrue(self.valid(b,c));self.assertEqual(wire.response(b,c),(0,b'test'))
  rng=random.Random(960);offsets=[0,0x1ffff,0x20000,wire.MUTABLE_START-1,wire.MUTABLE_END,0x6ffff,524287]
  offsets += [rng.randrange(wire.MUTABLE_START) for _ in range(100)]
  offsets += [rng.randrange(wire.bio.IMAGE_SIZE,524288) for _ in range(100)]
  for offset in offsets:
   c=bytearray(a);c[offset]^=1;self.assertFalse(self.valid(b,c),hex(offset))
   with self.assertRaises(ValueError):wire.response(b,c)
 def test_malformed_response(self):
  b,a=self.images()
  for off,val in [(20,0xffffffff),(24,8193),(28,2),(0,0)]:
   c=bytearray(a);struct.pack_into('<I',c,wire.bio.OFFSET+off,val);self.assertFalse(self.valid(b,c))
  c=bytearray(a);c[wire.bio.OFFSET+wire.bio.OUTPUT+4]^=1;self.assertFalse(self.valid(b,c))
 def test_prepare_bounds(self):
  with self.assertRaises(ValueError):wire.prepare(bytes(wire.MUTABLE_END+4))
  with self.assertRaises(ValueError):wire.block(bytes(4097),1)
  with self.assertRaises(ValueError):wire.block(b'',0)
if __name__=='__main__':unittest.main()
