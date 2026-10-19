import sys
from pathlib import Path
from qlogic_firmware import audit
b=Path(sys.argv[1]).read_bytes()
assert not audit(b)['memory_reclaimable']
for off in (0,0x5ae18,len(b)-1):
 t=bytearray(b);t[off]^=1
 try:audit(t)
 except ValueError:pass
 else:raise AssertionError(off)
print('QLogic static dependencies: exact runtime accepted; corrupted runtime rejected')
