#!/usr/bin/env python3
"""Exercise the exact target C protocol through a native shared library."""
import ctypes as C
import os,random,struct,subprocess,tempfile,unittest
from pathlib import Path
from protocol import request,response
HERE=Path(__file__).resolve().parent
U=C.c_uint32
Slot=U*16
class State(C.Structure):_fields_=[('epoch',U),('sequence',U),('heartbeat',U),('stopped',U)]
Barrier=C.CFUNCTYPE(None,C.c_void_p)
Quiesce=C.CFUNCTYPE(C.c_int,C.c_void_p)
class Hooks(C.Structure):_fields_=[('barrier',Barrier),('quiesce',Quiesce),('arg',C.c_void_p)]

class Test(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();lib=Path(cls.tmp.name)/'control.so'
  subprocess.run([os.environ.get('CC','cc'),'-std=c99','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-shared','-fPIC',str(HERE/'control.c'),'-o',str(lib)],check=True)
  cls.lib=C.CDLL(str(lib));cls.lib.ctl_init.argtypes=[C.POINTER(State),U]
  cls.lib.ctl_poll.argtypes=[C.POINTER(State),C.POINTER(U),C.POINTER(U),C.POINTER(Hooks)]
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def setUp(self):
  self.state=State();self.assertEqual(self.lib.ctl_init(C.byref(self.state),123),1)
  self.req=Slot();self.res=Slot();self.calls=0;self.allow=True
  def stop(_):self.calls+=1;return int(self.allow)
  self.barrier=Barrier(lambda _:None);self.stop=Quiesce(stop);self.hooks=Hooks(self.barrier,self.stop,None)
 def send(self,seq,op=0,arg=0,epoch=123):
  self.req[:]=struct.unpack('<16I',request(epoch,seq,op,arg))
  return self.lib.ctl_poll(C.byref(self.state),self.req,self.res,C.byref(self.hooks))
 def result(self,seq):return response(bytes(self.res),123,seq)
 def test_ping_stop_duplicate_and_post_stop(self):
  self.lib.ctl_tick(C.byref(self.state));self.send(1,1,0xdeadbeef)
  self.assertEqual(self.result(1),dict(status=0,value=0xdeadbeef,stopped=False,heartbeat=1))
  self.send(2,2);self.assertTrue(self.result(2)['stopped']);self.assertEqual(self.calls,1)
  self.assertEqual(self.send(2,2),0);self.assertEqual(self.calls,1)
  self.lib.ctl_tick(C.byref(self.state));self.send(3,1);self.assertEqual(self.result(3)['status'],6)
  self.send(4,0);self.assertEqual(self.result(4)['heartbeat'],1)
 def test_epoch_sequence_and_stop_failure(self):
  self.send(1,2,epoch=124);self.assertEqual(self.result(1)['status'],2);self.assertEqual(self.calls,0)
  self.send(2,2);self.assertEqual(self.result(2)['status'],3);self.assertEqual(self.calls,0)
  self.allow=False;self.send(1,2);self.assertEqual(self.result(1)['status'],5);self.assertFalse(self.state.stopped)
  self.allow=True;self.send(2,2);self.assertTrue(self.state.stopped)
 def test_corruption_and_torn_publication(self):
  valid=request(123,1,2)
  for index in range(4,64):
   self.req[:]=struct.unpack('<16I',valid);raw=bytearray(valid);raw[index]^=1;self.req[:]=struct.unpack('<16I',raw)
   self.lib.ctl_poll(C.byref(self.state),self.req,self.res,C.byref(self.hooks))
   self.assertEqual(self.calls,0);self.assertEqual(self.state.sequence,0)
  self.req[:]=struct.unpack('<16I',valid)
  barrier=Barrier(lambda _:self.req.__setitem__(0,0));hooks=Hooks(barrier,self.stop,None)
  self.assertEqual(self.lib.ctl_poll(C.byref(self.state),self.req,self.res,C.byref(hooks)),0)
  self.assertEqual(self.calls,0)
 def test_unknown_operation_wrap_and_fuzz(self):
  self.send(1,99);self.assertEqual(self.result(1)['status'],4)
  self.state.sequence=0xffffffff;self.send(1,2);self.assertEqual(self.result(1)['status'],3)
  rng=random.Random(1960)
  for _ in range(10000):
   self.req[:]=[rng.getrandbits(32) for _ in range(16)]
   self.lib.ctl_poll(C.byref(self.state),self.req,self.res,C.byref(self.hooks))
  self.assertEqual(self.calls,0)
 def test_host_rejects_stale_or_corrupt_response(self):
  self.send(1)
  with self.assertRaises(ValueError):response(bytes(self.res),124,1)
  raw=bytearray(bytes(self.res));raw[28]^=1
  with self.assertRaises(ValueError):response(raw,123,1)

if __name__=='__main__':unittest.main()
