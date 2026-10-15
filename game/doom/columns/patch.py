"""Exact pinned-source transformation, preserving setup and range checks."""
def apply(src,patch,fixed=False):
 patch('r_draw.c','#include "bounded_column.h"','#include "bounded_column.h"\n#include "column.h"')
 text=(src/'r_draw.c').read_text()
 for name,low in [('R_DrawColumn',False),('R_DrawColumnLow',True)]:
  start=text.index('void '+name+' (void)')
  end=text.index('\n}',start)+2
  body=text[start:end]
  # Keep the baseline body and inject dispatch immediately before its loop.
  marker='    do'
  assert body.count(marker)==1
  code='''    if (doom_column_mode) {
        struct doom_column_job j;
        j.dst=dest;j.dst2=DEST2;j.source=dc_source;j.map=dc_colormap;
        j.frac=(unsigned)frac;j.step=(unsigned)fracstep;
        j.count=(unsigned)count+1;j.post_length=dc_postlength;
        if(doom_column_mode==1)doom_column_c(&j);else doom_column_asm(&j);
        return;
    }
'''.replace('DEST2','dest2' if low else '0')
  if fixed:
   code=code.replace('if (doom_column_mode)', 'if (1)').replace('if(doom_column_mode==1)doom_column_c(&j);else doom_column_asm(&j);','doom_column_c(&j);')
  patch('r_draw.c',body,body.replace(marker,code+marker))
