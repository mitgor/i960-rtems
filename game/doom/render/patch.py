"""Preserve original span setup, endpoint convention and low-detail side effects."""
def apply(src,patch):
 patch('r_draw.c','#include "bounded_column.h"','#include "bounded_column.h"\n#include "span.h"')
 text=(src/'r_draw.c').read_text()
 for name,low in [('R_DrawSpan',0),('R_DrawSpanLow',1)]:
  start=text.index('void '+name+' (void)');end=text.index('\n}',start)+2
  body=text[start:end];begin=body.index('    do\n');finish=body.index('    } while (count--);',begin)+len('    } while (count--);')
  replacement='    doom_span(dest,ds_source,ds_colormap,position,step,(unsigned)count+1,'+str(low)+');'
  patch('r_draw.c',body,body[:begin]+replacement+body[finish:])
