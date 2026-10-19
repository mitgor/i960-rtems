import struct
from qlogic_queue import decode
w=[0]*1024
w[352:374]=[0x314d5251,1,23,4,0,0,0xc0600d00,14,0x8bf00000,0,0,0xc0600df0,256,0xc0604df0,128,0xc0600df0,0xc0604df0,0,0,0,0,0]
pack=lambda x:struct.pack('<1024I',*x)
r=decode(pack(w),23,4,0)
assert r['expected_layout'] and r['ring_pointers_in_range'] and r['indices_in_range'] and not r['hardware_drained']
for i in list(range(352,360))+list(range(374,384)):
 t=w.copy();t[i]^=1
 try:decode(pack(t),23,4,0)
 except ValueError:pass
 else:raise AssertionError(i)
t=w.copy();t[369]=0xffff0001;t[367]=0xdeadbeef;t[361]=0xdeadbeef
r=decode(pack(t),23,4,0)
assert not r['indices_in_range'] and not r['ring_pointers_in_range'] and not r['ownership_proven']
print('QLogic RAM decoder: tampering rejected; unknown pointers/indices remain observations, never dereferenced')

# Actual capture crosses the previous size hypothesis; bounds use confirmed sizes.
t=w.copy();t[367]=0xc0600df0+255*64;t[368]=0xc0604df0+127*64;t[369]=255|(255<<16);t[370]=127|(127<<16)
r=decode(pack(t),23,4,0)
assert r['expected_layout'] and r['ring_pointers_in_range'] and r['indices_in_range']
