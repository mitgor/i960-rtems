#!/usr/bin/env python3
"""Read-only bootstrap/decode evidence. Never converts a mapping into a RAM grant."""
import argparse,hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def bootstrap(out):
 root=ROOT/'artifacts/vendor-fujitsu/4.07-0-29';b=(root/'Fgj40729.img.raw').read_bytes();rows=[]
 for line in (root/'bootstrap.dis').read_text().splitlines():
  m=re.match(r'^([0-9a-f]{8}):\s*((?:[0-9a-f]{2} ){3}[0-9a-f]{2})\s*(.*)$',line)
  if m:
   pc=int(m[1],16);assert b[pc-0xfefc8000:pc-0xfefc8000+4]==bytes.fromhex(m[2]);rows.append((pc,line))
 for name,lo,hi in [('board-select',0xfefcb460,0xfefcb540),('internal-dispatch',0xfefcc1f0,0xfefcc310),('external-dispatch',0xfefcc310,0xfefcc4a4),('cpu-xor',0xfefcc540,0xfefcc660)]:
  (out/(name+'.txt')).write_text('\n'.join(line for pc,line in rows if lo<=pc<hi)+'\n')
 return dict(bootstrap_sha256=hashlib.sha256(b).hexdigest(),byte_checked_rows=len(rows),board_selector='(read8(e0400000) & 31) == 6',internal_install='fefcc1f0',external_install='fefcc310',internal_xor_runtime='c000d540',internal_xor_flash='fefcc540',external_submit=['c004e940','c004ea80'],completion='internal CPU XOR returns synchronously; external bit-0 handshake is a different dispatch',whole_engine_drain_proven=False)
def decode(pages):
 assert len(pages) in (4,6,7)
 for i,w in enumerate(pages,1):assert len(w)==160 and w[150:152]==[0x32484343,i]
 p={i+1:w[152:] for i,w in enumerate(pages)}
 assert p[4][:4]==[0xa5a5a5a5,0x5a5a5a5a,0xa5a5,0x5a5a] and p[4][4]==p[4][5]==p[1][7]
 bcon=p[1][6];dbcr=p[3][0]
 result=dict(positive_controls=True,pmcon45=hex(p[1][2]),pmcon1415=hex(p[1][5]),bcon=hex(bcon),pmcon_table_valid=bool(bcon&4),atucr=hex(p[1][7]),direct_address_mode=bool(p[1][7]&256),dbcr=hex(dbcr),dram_base=hex(p[3][1]),dram_enabled=bool(dbcr&1),dram_arrangement_field=(dbcr>>3)&31,dram_bank_leaf_mib=[1,4,16,64][(dbcr>>1)&3],installed_ram_bytes=None,cache_reads=[hex(v) for v in p[3][6:]],nmisr=hex(p[4][7]),broader_ram_owned=False)
 if len(pages)>=6:
  expected=[0xc004fe20,0xc004c3b0,0xc004c3b0,0xc004fe50,0xc004fe80,0xc004c3b0,0xc004c3b0,0xc004feb0]
  result.update(table=hex(p[5][0]),alias_base=hex(p[5][1]),dispatch_170_18c=[hex(v) for v in p[6]],internal_dispatch_subset_matches=p[6]==expected)
 if len(pages)==7:
  result['dispatch_identity']=[hex(v) for v in p[7]]
  result['internal_cpu_path_qualified']=bool(result['internal_dispatch_subset_matches'] and p[7][0]&31==6 and p[7][1:4]==[0xc000d540,0xc004fc40,0xc0050430] and p[7][6:]==[0xe0600000,0xe0600005])
  result['firmware_detected_ram_bytes']=p[7][4]
  result['installed_ram_bytes']=None # firmware report is not a destructive capacity/alias test
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--pages',type=Path);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 r=bootstrap(a.out)
 if a.pages:r['live']=decode(json.loads(a.pages.read_text()))
 (a.out/'decode.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
