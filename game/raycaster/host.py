import ctypes
import struct
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
MAGIC=0x31594152
PALETTE=['#25394c','#403d38','#d88254','#a65435','#66b28d','#357759','#699aca','#426b9f','#c9b971','#8d7b43']
def request(op=1,columns=80,keys=0,pixels=1,kind=0,reps=0):
    return struct.pack('<8I',MAGIC,op,columns,keys,pixels,kind,reps,0)
def decode(data):
    if len(data) not in (64,4864):raise ValueError('reply size')
    h=struct.unpack('<16I',data[:64])
    if h[0]!=MAGIC or h[9]!=len(data)-64:raise ValueError('reply header')
    return dict(frame_id=h[1],column=h[2],x=h[3],y=h[4],angle=h[5],dda_steps=h[6],hash=h[7],digest=h[8],kind=h[10],reps=h[11],frame=data[64:].hex(),palette=PALETTE)
class Native:
    def __init__(self):
        self.lib=ctypes.CDLL(str(HERE/'build/libray.so'))
        self.lib.ray_size.restype=ctypes.c_uint
        self.lib.ray_request.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint]
        self.lib.ray_request.restype=ctypes.c_uint
        self.state=ctypes.create_string_buffer(self.lib.ray_size())
    def step(self,data):
        out=ctypes.create_string_buffer(4864)
        rc=self.lib.ray_request(self.state,ctypes.create_string_buffer(data),len(data),out,4864)
        if rc:raise ValueError(f'RAY1 rejected: {rc}')
        n=struct.unpack_from('<I',out.raw,36)[0]
        return out.raw[:64+n]
    def close(self):pass
def card_backend(payload,module,output):
    sys.path.insert(0,str(HERE.parents[1]/'rtems/transport'))
    from run import Board
    return Board(payload,module,output)
