from test_qlogic_pause import w,pack
from qlogic_dma_bank import decode
w[464:476]=[0x31424451,1,23,1,0,0x44,0x344,0x344,0x44,0x20,2,12]
w[480:492]=[0x15,0,0,0x15,0,0]*2
r=decode(pack(w),23,3,1)
assert r['samples_equal'] and not r['ownership_proven'] and not r['hardware_drained']
for i in list(range(464,480))+list(range(492,512)):
 t=w.copy();t[i]^=1
 try:decode(pack(t),23,3,1)
 except ValueError:pass
 else:raise AssertionError(i)
t=w.copy();t[491]=65536
try:decode(pack(t),23,3,1)
except ValueError:pass
else:raise AssertionError('width')
t=w.copy();t[491]=1
assert not decode(pack(t),23,3,1)['samples_equal']
print('DMA bank decoder: strict envelope, restoration, retained origin, bounded register widths; unequal snapshots remain observations')
