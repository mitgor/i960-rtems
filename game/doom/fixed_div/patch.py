"""Stable per-source-call-site profiling; no approximate division."""
import re,json,shutil
from pathlib import Path
def apply(src,patch,fast,profile=True):
 here=Path(__file__).resolve().parent
 patch('m_fixed.c','fixed_t FixedDiv(fixed_t a, fixed_t b)','fixed_t doom_div_legacy(fixed_t a, fixed_t b)')
 if not profile:
  assert fast
  # Preserve every call site and the original ABI; omit timers and self-tests.
  with (src/'m_fixed.c').open('a') as out:
   out.write('\nextern int doom_div_fast(int,int);\nfixed_t FixedDiv(fixed_t a,fixed_t b){return doom_div_fast(a,b); }\n')
  for name in ('divide.c','divide.S'):shutil.copyfile(here/name,src/('fixed_'+name))
  return
 sites=[]
 for f in sorted(src.glob('*.c')):
  if f.name=='m_fixed.c':continue
  text=f.read_text()
  # Calls have two operands: add site via a per-site macro to preserve parsing.
  for match in list(re.finditer(r'\bFixedDiv\s*\(',text))[::-1]:
   site=len(sites);sites.append(dict(id=site,file=f.name,line=text[:match.start()].count('\n')+1))
   text=text[:match.start()]+f'DOOM_DIV_{site}('+text[match.end():]
  f.write_text(text)
 assert len(sites)==47, "pinned source site schema changed"
 header='#ifndef DOOM_FIXED_PROFILE_H\n#define DOOM_FIXED_PROFILE_H\n#define FD_SITES %d\nint doom_div_profile(int,int,unsigned);\nint doom_div_check(void);\nvoid doom_div_record(unsigned*);\n'%len(sites)
 for s in sites:header+=f'#define DOOM_DIV_{s["id"]}(a,b) doom_div_profile((a),(b),{s["id"]}u)\n'
 header+='#endif\n'
 (src/'fixed_profile.h').write_text(header)
 patch('m_fixed.h','#define __M_FIXED__','#define __M_FIXED__\n#include "fixed_profile.h"')
 # Keep external FixedDiv ABI for any non-call references.
 with (src/'m_fixed.c').open('a') as out:out.write('\nfixed_t FixedDiv(fixed_t a,fixed_t b){return doom_div_legacy(a,b);}\n')
 for name in ('divide.c','divide.S','profile.c'):shutil.copyfile(here/name,src/('fixed_'+name))
 (src/'fixed-sites.json').write_text(json.dumps(sites,indent=2)+'\n')
