import struct
from qlogic_config import decode
w=[0]*1024
w[320:340]=[0x31494350,1,12,3,0,0,0x10014,0x10014,5,0,0x10161077,7,0x1000000,0,0xfff00000,0,0,0,0,0]
pack=lambda x:struct.pack('<1024I',*x)
assert not decode(pack(w),12,3,0)['ownership_proven']
for i in list(range(320,331))+[334,335,339]:
 t=w.copy();t[i]^=1
 try:decode(pack(t),12,3,0)
 except ValueError:pass
 else:raise AssertionError(i)
print('QLogic decoder rejects stale identity, incomplete/failed restore, wrong BAR and reserved tampering')
