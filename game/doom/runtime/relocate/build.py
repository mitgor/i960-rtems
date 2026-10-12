#!/usr/bin/env python3
"""Generate a trusted, closed relocation recipe after independent linker checks."""
import argparse,json,struct,subprocess
from pathlib import Path
from pack import rebase
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--cross',required=True);a=p.parse_args()
subprocess.run(['python3',str(Path(__file__).with_name('test.py')),'--out',str(a.out),'--cross',a.cross],check=True)
b,m=rebase((a.out/'probe.o').read_bytes(),0)
assert [s['name'] for s in m['sections']]==['.text','.data','.bss']
# This is a reviewed probe, not a general ELF admission mechanism.
assert m['sections'][2]['memory_bytes']==128
nm=subprocess.check_output([a.cross+'nm',str(a.out/'probe.o')],text=True)
symbols={row.split()[2]:(int(row.split()[0],16),row.split()[1]) for row in nm.splitlines() if len(row.split())==3}
for name,section in (('_seed',1),('_selected',1),('_counts',2)):
 m[name[1:]+'_offset']=m['sections'][section]['offset']+symbols[name][0]
assert struct.unpack_from('<I',b,m['seed_offset'])[0]==0x49393630
assert struct.unpack_from('<I',b,m['selected_offset'])[0]==m['counts_offset']+12
m['sha256']=__import__('hashlib').sha256(b).hexdigest()
(a.out/'template.bin').write_bytes(b);(a.out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
s='static const unsigned char relocated_bytes[]={'+','.join(map(str,b))+'};\n'
s+='static const unsigned int relocated_sites[]={'+','.join(map(str,m['relocations']))+'};\n'
for k,v in {'ENTRY':m['entry'],'SPAN':m['memory_bytes'],'TEXT':m['sections'][0]['file_bytes'],'DATA':m['sections'][1]['offset'],'DATA_BYTES':m['sections'][1]['file_bytes'],'BSS':m['sections'][2]['offset'],'SEED':m['seed_offset'],'SELECTED':m['selected_offset'],'COUNTS':m['counts_offset']}.items():s+=f'#define RELOC_{k} {v}u\n'
(a.out/'relocated_probe_bytes.h').write_text(s)
