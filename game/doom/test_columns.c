/* Link the actual patched renderer with --gc-sections; no game simulation. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdarg.h>
#include "r_local.h"
#include "bounded_column.h"
extern int dc_postlength;
extern byte *ylookup[];
extern int columnofs[];
int centery;
void I_Error(const char *format, ...)
{
    va_list args;va_start(args,format);vfprintf(stderr,format,args);va_end(args);
    abort();
}
int main(void)
{
    static byte frame[320*200], source[256], map[256], translation[256];
    int n, i, mode;
    for (i=0;i<256;i++) { source[i]=(byte)i;map[i]=(byte)i;translation[i]=(byte)(255-i); }
    for (i=0;i<200;i++) ylookup[i]=frame+i*320;
    for (i=0;i<320;i++) columnofs[i]=i;
    dc_source=source;dc_colormap=map;dc_translation=translation;
    dc_x=2;dc_yl=0;dc_yh=2;dc_iscale=65536;centery=0;
    for (n=1;n<=255;n++) {
        assert(R_ColumnIndex(-1,n,1)==0);
        assert(R_ColumnIndex(n*65536,n,1)==n-1);
        for (i=0;i<n;i++) assert(R_ColumnIndex(i*65536,n,1)==i);
        for (mode=0;mode<4;mode++) {
            memset(frame,0x55,sizeof(frame));dc_postlength=n;dc_texturemid=-1;
            if(mode==0)R_DrawColumn();
            if(mode==1)R_DrawColumnLow();
            if(mode==2)R_DrawTranslatedColumn();
            if(mode==3)R_DrawTranslatedColumnLow();
            for(i=0;i<3;i++) {
                int x=(mode&1)?4:2;
                byte expected=(byte)R_ColumnIndex(-1+i*65536,n,1);
                if(mode>=2)expected=255-expected;
                assert(frame[i*320+x]==expected);
                if(mode&1)assert(frame[i*320+x+1]==expected);
            }
            dc_texturemid=n*65536;
            if(mode==0)R_DrawColumn();
            if(mode==1)R_DrawColumnLow();
            if(mode==2)R_DrawTranslatedColumn();
            if(mode==3)R_DrawTranslatedColumnLow();
            for(i=0;i<3;i++) {
                int x=(mode&1)?4:2;
                byte expected=(byte)(mode>=2?256-n:n-1);
                assert(frame[i*320+x]==expected);
                if(mode&1)assert(frame[i*320+x+1]==expected);
            }
        }
    }
    dc_postlength=0;dc_texturemid=-1;R_DrawColumn();
    assert(frame[2]==127&&frame[322]==0&&frame[642]==1);
    dc_texturemid=128*65536;R_DrawColumn();
    assert(frame[2]==0&&frame[322]==1&&frame[642]==2);
    puts("All post lengths 1..255, both edges, normal/low/translated drawers, and wall wrapping pass");
    return 0;
}
