#!/usr/bin/env python3
"""Verify exact firmware bytes before emitting completion leads; never grants RAM."""
import argparse,hashlib,json,re
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
b=root/'artifacts/vendor-fujitsu/4.07-0-29';blob=(b/'unpacked.bin').read_bytes();digest=hashlib.sha256(blob).hexdigest()
assert digest=='21f6c1d898a533d7023a53893f03547ed61631016d1b247d3ecbb97b9403c195'
assert blob==(root/'artifacts/private-dumps/snapshot-fresh-20261010T125336Z/firmware-unpacked.bin').read_bytes()
rows=[];checked=0
for line in (b/'unpacked.dis').read_text().splitlines():
 m=re.match(r'^([0-9a-f]{8}):\s*((?:[0-9a-f]{2} ){3}[0-9a-f]{2})\s*(.*)$',line)
 if m:
  pc=int(m[1],16);assert bytes.fromhex(m[2])==blob[pc-0xc0010000:pc-0xc0010000+4];rows.append((pc,line));checked+=1
ranges=[('submit-wait-ack-results',0xc004e940,0xc004ea54),('dma-and-cache-completion',0xc004ea80,0xc004ecf0),('error-service',0xc004efd0,0xc004f14c),('status-mask-ack',0xc004ff70,0xc0050238),('board-timer',0xc0050300,0xc00503c0)]
for name,lo,hi in ranges:(a.out/(name+'.txt')).write_text('\n'.join(l for pc,l in rows if lo<=pc<hi)+'\n')
claims={
 'completion':{'submit_pc':'c004e9c8','command_register':'4080001c','wait_pc':'c004e9d8','status_register':'40800008','access_bits':16,'wait_bit':0,'wait_until_set':True,'ack_pc':'c004e9ec','ack_value':1},
 'status_mask_pair':{'pc':'c004ff88','status':'40800008','mask':'4080000a','access_bits':16},
 'timer_completion':{'pc':'c0050344','status_bit':5,'not_cache_completion':True},
 'limitations':['linear disassembly is not a full reachability proof','completion after a submitted command is not a global idle predicate','status=0 may mean acknowledged completion or work in flight','queue ownership, command semantics, active drain, cache identity and SCSI drain remain unresolved','no cache control, mask, command or acknowledgement writes are implemented'],
 'broader_ram_owned':False,'cache_engine_drained':False}
(a.out/'audit.json').write_text(json.dumps(dict(firmware_sha256=digest,matching_dump=True,byte_checked_rows=checked,**claims),indent=2)+'\n')
print(f'{checked} byte-checked rows; completion sequence located; global drain and RAM reclamation remain denied')
