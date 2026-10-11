#!/usr/bin/env python3
"""Byte-checked matching-firmware DMA leads; no inferred ownership from absence."""
import hashlib,json,re,struct,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'artifacts/vendor-fujitsu/4.07-0-29'
REGS={0x1400:'DMA0 control',0x1404:'DMA0 status',0x1410:'DMA0 descriptor',0x1440:'DMA1 control',0x1444:'DMA1 status',0x1450:'DMA1 descriptor',0x1480:'DMA2 control',0x1484:'DMA2 status',0x1490:'DMA2 descriptor'}
RANGES=[('dma-init',0xc004b790,0xc004b81c),('dma0-start-completion',0xc004bf08,0xc004c000),('dma1-start-wait-stop',0xc004c090,0xc004c134),('io-descriptor-lead',0xc002fbdc,0xc002fc30)]
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
blob=(BASE/'unpacked.bin').read_bytes();sha=hashlib.sha256(blob).hexdigest();assert sha=='21f6c1d898a533d7023a53893f03547ed61631016d1b247d3ecbb97b9403c195'
assert blob==(ROOT/'artifacts/private-dumps/snapshot-fresh-20261010T125336Z/firmware-unpacked.bin').read_bytes()
rows=[];hits=[]
for line in (BASE/'unpacked.dis').read_text().splitlines():
 m=re.match(r'^([0-9a-f]{8}):\s*((?:[0-9a-f]{2} ){3}[0-9a-f]{2})\s*(.*)$',line)
 if not m:continue
 pc=int(m[1],16);assert blob[pc-0xc0010000:pc-0xc0010000+4]==bytes.fromhex(m[2]);rows.append((pc,line))
 if re.match(r'(lda|ld|st|ldob|stob|ldos|stos|ldl|stl|ldt|stt|ldq|stq)\s',m[3]):
  for lit in re.findall(r'0x([0-9a-f]+)',m[3]):
   v=int(lit,16)
   if v in REGS:hits.append(dict(pc=hex(pc),register=REGS[v],asm=m[3]))
for name,lo,hi in RANGES:(a.out/(name+'.txt')).write_text('\n'.join(line for pc,line in rows if lo<=pc<hi)+'\n')
(a.out/'audit.json').write_text(json.dumps(dict(sha256=sha,matches_actual_dump=True,byte_checked_rows=len(rows),direct_leads=hits,primary_channels_used_by_firmware=[0,1],dma2_release_contract=False,scsi_quiescence_contract=False,ownership_granted=False,limitations=['linear disassembly may contain data','indirect/computed references are not exhausted','DMA0/1 start/completion excerpts prove stock use, not a callable release API','no direct DMA2 hit would not prove unused','descriptor-looking A0000000/A1000000 values are not a proven SCSI MMIO map']),indent=2)+'\n')
print(f'Checked {len(rows)} source rows against matching ROM; {len(hits)} direct DMA-register leads. No DMA/SCSI ownership granted.')
