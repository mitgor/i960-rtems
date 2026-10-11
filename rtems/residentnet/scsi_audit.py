#!/usr/bin/env python3
"""Byte-checked firmware channel topology; metadata is not reset/drain proof."""
import argparse,hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--pages',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
f=ROOT/'artifacts/vendor-fujitsu/4.07-0-29';b=(f/'unpacked.bin').read_bytes();sha=hashlib.sha256(b).hexdigest();assert sha=='21f6c1d898a533d7023a53893f03547ed61631016d1b247d3ecbb97b9403c195'
rows=[]
for line in (f/'unpacked.dis').read_text().splitlines():
 m=re.match(r'^([0-9a-f]{8}):\s*((?:[0-9a-f]{2} ){3}[0-9a-f]{2})\s*(.*)$',line)
 if m:
  pc=int(m[1],16);assert b[pc-0xc0010000:pc-0xc0010000+4]==bytes.fromhex(m[2]);rows.append((pc,line))
for name,lo,hi in [('primary-symbios',0xc004f270,0xc004f4f4),('secondary-symbios',0xc004f500,0xc004f66d),('secondary-buslogic',0xc004f750,0xc004f810),('config-ports',0xc004f670,0xc004f750),('buslogic-config-write',0xc004e0f0,0xc004e120),('nmi-entry',0xc004e190,0xc004e214),('nmi-reinitialization',0xc004e2e8,0xc004e334)]:
 (a.out/(name+'.txt')).write_text('\n'.join(line.rstrip() for pc,line in rows if lo<=pc<hi)+'\n')
r=dict(firmware_sha256=sha,byte_checked_rows=len(rows),channel_count_address='c0060000',channel_base='c0083000',channel_stride='170',primary_flag_offset='3c',identity_offset='104',scsi_stopped=False,ram_granted=False)
if a.pages:
 pages=json.loads(a.pages.read_text());assert len(pages) in (28,29,31)
 for i,w in enumerate(pages,1):assert len(w)==160 and w[150:152]==[0x32484343,i]
 v={i+1:w[152:] for i,w in enumerate(pages)};count=v[16][0];assert 1<=count<=6
 channels=[]
 for i in range(count):
  x=v[17+2*i];y=v[18+2*i];identity=y[5]
  channels.append(dict(index=i,mmio=hex(x[0]),pci_bar=hex(x[1]),script_mmio=hex(x[3]),primary_flag=x[4],config_select=hex(x[5]),vendor=hex(identity&65535),device=hex(identity>>16),revision=y[6]&65535))
 r.update(channels=channels,secondary_count=v[16][2],bridge_bus_numbers=hex(v[16][5]),all_channels_secondary=all(c['primary_flag']==0 for c in channels),live_table=hex(v[16][1]))
if a.pages and len(pages)>=29:
 assert v[29][0]==0x000c1000 and v[29][2]&255==2 and v[29][3]==0xfff00000 and v[29][4]==0xfff02000 and v[29][5]==v[29][6]
 r['pci_config']=[hex(x) for x in v[29]]
 r['identity_corroborated']=True
if a.pages and len(pages)==31:
 observed=v[30];assert observed[0]==0xc004e190 and observed[1]==0xfeffd4d0
 # The diagnostic intentionally refuses a ROM pointer. Resolve the exact saved
 # PRCB from independently paired, programmed full-ROM captures instead.
 rom=ROOT/'artifacts/programmed-rom-20261010/programming/captures'
 raw=(rom/'flash-readback-5a.bin').read_bytes();assert raw==(rom/'flash-readback-a5.bin').read_bytes()
 digest=hashlib.sha256(raw).hexdigest();assert digest=='a898b30212e1f935339d91a1adfa84f6589a3136099aeda4ffa250981e4e28b0'
 data=raw[observed[1]-0xfef80000:observed[1]-0xfef80000+40];prcb=struct.unpack('<10I',data);assert prcb[0]==0xc0000800
 (a.out/'archived-prcb.bin').write_bytes(data)
 r['stock_async_paths']={'cached_nmi':hex(observed[0]),'prcb':hex(observed[1]),'live_fault_table_read':False,'diagnostic_skipped_rom_pointer':True,'fault_table_from_archived_rom':hex(prcb[0]),'rom_sha256':digest,'exclusive_ownership_proven':False}
(a.out/'topology.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
