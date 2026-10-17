"""Exact bounded native FNV; the caller verifies library identity before import."""
import ctypes
from pathlib import Path
lib=ctypes.CDLL(str(Path(__file__).with_name('fnv_host.so')))
call=lib.frame_fnv;call.argtypes=(ctypes.c_void_p,ctypes.c_size_t);call.restype=ctypes.c_uint32
def fnv(data):
 data=bytes(data)
 buffer=ctypes.create_string_buffer(data)
 return call(buffer,len(data))
def reference(data):
 h=2166136261
 for v in data:h=((h^v)*16777619)&0xffffffff
 return h
for data in (b'',b'a',bytes(range(256)),bytes(65536),b'\xff'*65536,
             bytes((i*17+13)%251 for i in range(65536)),bytes((i*37+3)%251 for i in range(524288))):
 assert fnv(data)==reference(data)
