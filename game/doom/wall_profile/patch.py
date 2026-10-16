"""Inclusive, nonrecursive region brackets against pinned source definitions."""
import re,shutil
from pathlib import Path
def apply(src,patch):
 here=Path(__file__).resolve().parent
 shutil.copyfile(here/'profile.h',src/'wall_profile.h')
 shutil.copyfile(here/'profile.c',src/'wall_profile.c')
 # Root only: recursive BSP calls remain untouched. Subsector and wall regions
 # nest, so subtraction partitions work without summing recursive intervals.
 patch('r_main.c','#include "r_local.h"','#include "r_local.h"\n#include "wall_profile.h"')
 patch('r_main.c','    R_RenderBSPNode (numnodes-1);','    {unsigned wall_begin=doom_wall_begin(); R_RenderBSPNode (numnodes-1); doom_wall_end(0,wall_begin);}')
 for file,name,args,call,site in [('r_bsp.c','R_Subsector','int num','num',1),('r_segs.c','R_StoreWallRange','int start, int stop','start,stop',2),('r_segs.c','R_RenderSegLoop','void','',3)]:
  text=(src/file).read_text()
  (src/file).write_text('void '+name+'('+args+');\n'+text)
  matches=list(re.finditer(r'void\s+'+name+r'\s*\([^)]*\)\s*\{',text))
  assert len(matches)==1,(file,name)
  old=matches[0].group();new=old.replace(name,name+'_profile_body',1)
  patch(file,old,new)
  with (src/file).open('a') as out:
   out.write('\n#include "wall_profile.h"\nvoid '+name+'('+args+'){unsigned begin=doom_wall_begin(); '+name+'_profile_body('+call+'); doom_wall_end('+str(site)+',begin);}\n')
