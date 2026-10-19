import struct
from qlogic_chip import decode
w=[0]*1024
w[320:340]=[0x31494350,1,23,4,0,0,0x10014,0x10014,5,0,0x10161077,6,0x1000006,1,0xfff00000,0,0,0,0,0]
w[352:374]=[0x314d5251,1,23,4,0,0,0xc0600d00,14,0x8bf00000,0,0,0xc0600df0,256,0xc0604df0,128,0xc0601730,0xc0605370,37,22|(22<<16),0,0,578]
w[384:404]=[0x31504351,1,23,4,0,0,12,0]+[0,0,37,22,0,0]*2
pack=lambda v:struct.pack('<1024I',*v)
r=decode(pack(w),23,4,0)
assert r['stable'] and r['status_zero'] and r['request_ring_equal_observed'] and not r['request_consumer_matches_cache'] and not r['hardware_drained']
for i in list(range(384,392))+list(range(404,416))+[360]:
 t=w.copy();t[i]^=1
 try:decode(pack(t),23,4,0)
 except ValueError:pass
 else:raise AssertionError(i)
t=w.copy();t[331]=4
try:decode(pack(t),23,4,0)
except ValueError:pass
else:raise AssertionError('memory decoding')
t=w.copy();t[400]=38
assert not decode(pack(t),23,4,0)['stable']
t=w.copy();t[393]=1
assert not decode(pack(t),23,4,0)['status_zero']
t=w.copy();t[400]=65536
try:decode(pack(t),23,4,0)
except ValueError:pass
else:raise AssertionError('width')
print('chip decoder: stale cache distinguished, instability/status retained, envelope and width rejected')
