"""Native execution of the same real-time CHIP-8 player used by RTEMS."""
import ctypes
from pathlib import Path
class Player:
    def __init__(self,rom,hz=500,now=0,seed=1,library=None):
        self.lib=ctypes.CDLL(str(library or Path(__file__).resolve().parents[1]/'build/libplayer.so'))
        self.lib.c8_player_size.restype=ctypes.c_uint
        self.lib.c8_player_init.argtypes=[ctypes.c_void_p,ctypes.c_void_p,*([ctypes.c_uint]*4)]
        self.lib.c8_player_key.argtypes=[ctypes.c_void_p,ctypes.c_uint]
        self.lib.c8_player_update.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p]
        self.state=ctypes.create_string_buffer(self.lib.c8_player_size())
        if not self.lib.c8_player_init(self.state,rom,len(rom),seed,hz,now&0xffffffff):raise ValueError('CHIP-8 ROM/clock')
    def key(self,event):
        if type(event) is not int or not 0<=event<=511 or not self.lib.c8_player_key(self.state,event):raise ValueError('CHIP-8 key')
    def update(self,now):
        out=ctypes.create_string_buffer(512)
        result=self.lib.c8_player_update(self.state,now&0xffffffff,out)
        if result>1:raise RuntimeError('bounded CHIP-8 player stopped: '+str(result))
        return out.raw if result else None
