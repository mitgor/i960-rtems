#!/usr/bin/env python3
"""Pinned static allocator evidence plus read-only live metadata; never grants RAM."""
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--pages',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
v=ROOT/'artifacts/vendor-fujitsu/4.07-0-29';b=(v/'unpacked.bin').read_bytes()
sha=hashlib.sha256(b).hexdigest();assert sha=='21f6c1d898a533d7023a53893f03547ed61631016d1b247d3ecbb97b9403c195'
rows=[]
for line in (v/'unpacked.dis').read_text().splitlines():
 m=re.match(r'^([0-9a-f]{8}):\s*((?:[0-9a-f]{2} ){3}[0-9a-f]{2})\s*(.*)$',line)
 if m:
  pc=int(m[1],16);assert b[pc-0xc0010000:pc-0xc0010000+4]==bytes.fromhex(m[2]);rows.append((pc,line))
for name,lo,hi in [('staging-helper',0xc004d230,0xc004d300),('cache-reservation',0xc001ea70,0xc001ec40),('cache-geometry',0xc001c5a0,0xc001ccd0),('scsi-debug-counters',0xc0010dc0,0xc0010dec),('scsi-busy-test',0xc004a260,0xc004a2c0),('scsi-completion-count',0xc004bb20,0xc004bb80),('scsi-submit-count',0xc0051640,0xc00516d0),('transfer-dispatch',0xc00209b0,0xc0020b00),('script-command-construction',0xc002fc00,0xc002fce0)]:
 (a.out/(name+'.txt')).write_text('\n'.join(line for pc,line in rows if lo<=pc<hi)+'\n')
pages=json.loads(a.pages.read_text());assert len(pages) in (14,15)
for i,w in enumerate(pages,1):assert len(w)==160 and w[150:152]==[0x32484343,i]
v={i+1:w[152:] for i,w in enumerate(pages)}
ram=v[12][6];line=v[13][1]*512;count=v[9][0];desc=v[11][3];stage=v[13][2];size=v[10][2]
assert stage==0xc0f2c000 and size==0x80000
assert ram==0x1000000 and line==8192 and count==(ram-0x140040)//(line+52)
assert desc==0xc0140000+count*line and desc+count*52<=0xc0000000+ram
assert stage==0xc0140000+(v[9][1]-(size//line+1)-2)*line
r=dict(firmware_sha256=sha,byte_checked_rows=len(rows),firmware_ram_report=ram,line_bytes=line,line_count=count,data_start=hex(0xc0140000),descriptor_start=hex(desc),descriptor_bytes=52,descriptor_end=hex(desc+count*52),staging_start=hex(stage),staging_bytes=size,staging_line_index=(stage-0xc0140000)//line,adjacent_cache_bytes=desc-(stage+size),software_counters=None,broader_ram_owned=False,scsi_drained=False)
if len(pages)==15:r['software_counters']=dict(zip(['DrvQcnt','IodQcnt','SkedQcnt','ScsiIoCount'],v[15][3:7]))
(a.out/'allocation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
