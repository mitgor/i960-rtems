#!/usr/bin/env python3
"""Strict negative evidence for the reproduced frame-41 isolation halt."""
import hashlib,importlib.util,json,struct,sys,zlib
from pathlib import Path
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('fault',root/'rtems/dma/decode_frame_fault.py');fault=importlib.util.module_from_spec(spec);spec.loader.exec_module(fault)
p=Path(sys.argv[1]);out=p/'live';rows=lambda n:[json.loads(l) for l in (out/n).read_text().splitlines()]
f=rows('stress-frames.jsonl');reports=rows('frame-dma-results.jsonl');assert len(f)==len(reports)==40
pattern=lambda g:bytes(((i*13)^(i>>8)^(g*37))&255 for i in range(65536))
for g,(frame,report) in enumerate(zip(f,reports),1):
 raw=(out/f'frame-dma-{g:03}.bin').read_bytes();assert len(raw)==73728 and raw[:4096]==raw[69632:]==b'\xa5'*4096 and raw[4096:69632]==pattern(g)
 w=report['report'];assert w[:3]==[0x314d4446,2,g] and w[5]==w[6]==zlib.crc32(pattern(g)) and w[7]==w[9]==w[10]==w[13]==w[14]==0 and w[8]==w[15] and w[11]==7 and w[12]<200000
 assert frame['frame']==report['frame']==g and frame['sha256']==hashlib.sha256(pattern(g)).hexdigest()
records=rows('frame-dma-journal.jsonl');errors=[r for r in records if 'errno' in r and r['errno']!=11]
assert len(errors)==1 and errors[0] is records[-1] and errors[0]['errno']==110 and struct.unpack_from('<3I',bytes.fromhex(errors[0]['request']))[::2]==(2,41)
raw=(p/'retained-frame-dma.bin').read_bytes();assert len(raw)==73728 and raw[:4096]==raw[69632:]==b'\xa5'*4096 and raw[4096:69632]==pattern(41)
w=struct.unpack('<100I',(p/'retained-frame-fault.bin').read_bytes())[4:]
d=fault.decode((p/'retained-frame-fault.bin').read_bytes());assert d['terminal_identity_verified'] and d['trap_kind']==4 and d['diagnostic_rc']==0
assert w[48]==0x31504548 and w[51]==w[52]==1 and w[17]==0 and w[66]==41 and w[80]==7 and w[81]==49 and w[82]==w[84]==w[85]==0 and w[86]==1 and w[87]==6
assert not (out/'stress-result.json').exists()
print(json.dumps(dict(accepted=False,delivered_exact_frames=40,retained_unaccepted_frame=41,guards_intact=True,heap_error=1,scsi_isolation_valid=False,trap='software abort',dma_stage=7,poll_iteration=49,completion_timeout_errno=110),indent=2))
