/* Included after Doom types; definitions follow the declarations in r_draw.c. */
extern byte *ylookup[];
extern int columnofs[],dc_postlength;
extern byte *dc_translation;
#include "bounded_column.h"
static void half_column(unsigned translated)
{
    int y=(dc_yl+1)&~1, x=dc_x<<detailshift;
    unsigned frac,step,n;
    byte *dst;
    if(dc_yh<dc_yl)return;
    if(dc_yl<0 || dc_yh>=viewheight || dc_x<0 || dc_x>=viewwidth)
        I_Error("half column outside view");
    if(y>dc_yh)return;
    dst=ylookup[y]+columnofs[x];
    step=(unsigned)dc_iscale;
    frac=(unsigned)dc_texturemid+(unsigned)(y-centery)*step;
    n=(unsigned)(dc_yh-y)/2+1;step*=2;
    while(n--){
        int i=R_ColumnIndex((fixed_t)frac,dc_postlength,!translated);
        byte p=dc_source[i];
        if(translated)p=dc_translation[p];
        p=dc_colormap[p];dst[0]=p;if(detailshift)dst[1]=p;
        dst+=SCREENWIDTH*2;frac+=step;
    }
}
void R_HalfColumn(void){half_column(0);}
void R_HalfTranslated(void){half_column(1);}
void R_HalfExpand(void)
{
    int y,x;
    if(viewheight<1 || viewheight>SCREENHEIGHT || scaledviewwidth<1 ||
       scaledviewwidth>SCREENWIDTH || (scaledviewwidth&3))
        I_Error("half expansion outside view");
    /* R_InitBuffer gives 4-byte-aligned viewport starts. HUD is drawn later.
       Fuzz keeps its original guarded path; its odd outputs are discarded. */
    for(y=0;y+1<viewheight;y+=2){
        unsigned *src=(unsigned*)(ylookup[y]+columnofs[0]);
        unsigned *dst=(unsigned*)(ylookup[y+1]+columnofs[0]);
        for(x=0;x<scaledviewwidth/4;x++)dst[x]=src[x];
    }
}
