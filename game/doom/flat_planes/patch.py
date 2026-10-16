"""Optional solid visplanes; original textured and sky paths stay available."""
def apply(patch):
 patch('r_plane.c','#include "r_sky.h"','''#include "r_sky.h"
#include "flat_fill.h"
extern byte *ylookup[SCREENHEIGHT];
extern int columnofs[SCREENWIDTH];
unsigned doom_flat_planes,doom_flat_switches;
static unsigned doom_flat_held;
void doom_flat_key(unsigned down){
 if(down){if(!doom_flat_held){doom_flat_planes^=1;doom_flat_switches++;}doom_flat_held=1;}
 else doom_flat_held=0;
}''')
 patch('r_plane.c','    if (planeheight != cachedheight[y])','''    if (doom_flat_planes) {
        unsigned char color;
        if(x1<0 || x2<x1 || x2>=viewwidth || y<0 || y>=viewheight)
            I_Error("flat plane span outside view");
        color=(fixedcolormap ? fixedcolormap : planezlight[0])[ds_source[0]];
        doom_flat_fill(ylookup[y]+columnofs[x1<<detailshift],
                       (unsigned)(x2-x1+1)<<detailshift,color);
        return;
    }
    if (planeheight != cachedheight[y])''')
 patch('d_main.c','#include "doomstat.h"','#include "doomstat.h"\n#include "doomkeys.h"\nextern void doom_flat_key(unsigned);')
 patch('d_main.c','\tif (M_Responder (ev))','''        if ((ev->type==ev_keydown || ev->type==ev_keyup) && ev->data1==KEY_F6) {
            doom_flat_key(ev->type==ev_keydown);
            continue; /* quality control must not invoke quick-save */
        }
\tif (M_Responder (ev))''')
