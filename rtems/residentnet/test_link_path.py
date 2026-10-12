#!/usr/bin/env python3
"""Protected selection must depend on object names, not workspace names."""
import argparse,json,shutil,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--cross',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);rows=[]
script=Path(__file__).with_name('link-upload.ld');current=script.read_text()
selectors=' '.join('*/'+name+'.o(.text* .rodata*)' for name in ('doom_heap_core','doom_heap_libc','doom_heap_proof','doom_heap_shared','doom_runtime','doom_wad_core'))
assert current.count(selectors)==1
with tempfile.TemporaryDirectory(prefix='i960-link-',dir='/tmp') as temp:
 old=Path(temp)/'old.ld';old.write_text(current.replace(selectors,'*doom*.o(.text* .rodata*)'))
 for folder in ('plain-path','doom-workspace-path'):
  root=Path(temp)/folder;root.mkdir();objects=[]
  for name,text in [('normal_fixture','unsigned dummy;unsigned start(void){return 2;}'),('doom_fixture','unsigned protected_fixture(void){return 1;}')]:
   source=root/(name+'.c');source.write_text(text+'\n');obj=root/('doom_heap_core.o' if name=='doom_fixture' else 'app.o');subprocess.run([a.cross+'gcc','-mrp','-Os','-c',str(source),'-o',str(obj)],check=True);objects.append(obj)
  captures={}
  for label,linker in [('current',script),('old',old)]:
   elf=root/(label+'.elf');subprocess.run([a.cross+'ld','-T',str(linker),'-o',str(elf),*map(str,objects)],check=True)
   captures[label]={row.split()[2]:int(row.split()[0],16) for row in subprocess.check_output([a.cross+'nm',str(elf)],text=True).splitlines() if len(row.split())==3}
  symbols=captures['current'];assert 0xc0f2c000<=symbols['_start']<0xc0f4c000 and 0xc0f94000<=symbols['_protected_fixture']<0xc0f9bff0
  rows.append(dict(folder=folder,**captures));shutil.copytree(root,a.out/folder,dirs_exist_ok=True)
assert rows[0]['current']==rows[1]['current'] and rows[0]['old']['_start']!=rows[1]['old']['_start']
(a.out/'result.json').write_text(json.dumps(rows,indent=2)+'\n');print('PASS: explicit object selection independent of workspace path; original wildcard regression reproduced')
