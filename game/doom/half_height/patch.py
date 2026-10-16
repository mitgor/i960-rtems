"""Alternate-row shading with unchanged projection, clipping and view geometry."""
def apply(patch):
 patch('r_draw.c','#include "r_local.h"','#include "r_local.h"\n#include "half_height.h"')
 patch('r_main.c','#include "r_local.h"','''#include "r_local.h"
extern void R_HalfColumn(void),R_HalfTranslated(void),R_HalfExpand(void);
unsigned doom_half_height,doom_half_switches;
static unsigned doom_half_held;
void doom_half_key(unsigned down){
 if(down){if(!doom_half_held){doom_half_height^=1;doom_half_switches++;}doom_half_held=1;}
 else doom_half_held=0;
}''')
 patch('r_main.c','    R_SetupFrame (player);','''    /* Choose at a frame boundary, independently of F5 and F6. */
    colfunc = basecolfunc = doom_half_height ? R_HalfColumn :
        (detailshift ? R_DrawColumnLow : R_DrawColumn);
    transcolfunc = doom_half_height ? R_HalfTranslated :
        (detailshift ? R_DrawTranslatedColumnLow : R_DrawTranslatedColumn);
    R_SetupFrame (player);''')
 patch('r_main.c','    R_DrawMasked ();','    R_DrawMasked ();\n    if (doom_half_height) R_HalfExpand();')
 patch('r_plane.c','#include "r_sky.h"','#include "r_sky.h"\nextern unsigned doom_half_height;')
 patch('r_plane.c','    if (planeheight != cachedheight[y])','    if (doom_half_height && (y & 1)) return;\n    if (planeheight != cachedheight[y])')
 patch('d_main.c','#include "doomstat.h"','#include "doomstat.h"\n#include "doomkeys.h"\nextern void doom_half_key(unsigned);')
 patch('d_main.c','\tif (M_Responder (ev))','''        if ((ev->type==ev_keydown || ev->type==ev_keyup) && ev->data1==KEY_F7) {
            doom_half_key(ev->type==ev_keydown);
            continue; /* do not invoke end-game */
        }
\tif (M_Responder (ev))''')
