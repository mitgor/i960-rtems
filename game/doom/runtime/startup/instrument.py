"""Exact, recorded patches against the pinned Doom source; opt-in only."""
def apply(patch):
 for name in ('p_setup.c','r_data.c','r_main.c'):
  header='p_local.h' if name=='p_setup.c' else 'r_local.h'
  patch(name,'#include "'+header+'"','#include "'+header+'"\n#include "checkpoints.h"')
 patch('p_setup.c','    totalkills = totalitems', '    doom_platform_mark(10,episode,map,skill);\n    totalkills = totalitems')
 for stage,name,suffix,count in [(11,'BlockMap','BLOCKMAP','bmapwidth'),(12,'Vertexes','VERTEXES','numvertexes'),(13,'Sectors','SECTORS','numsectors'),(14,'SideDefs','SIDEDEFS','numsides'),(15,'LineDefs','LINEDEFS','numlines'),(16,'Subsectors','SSECTORS','numsubsectors'),(17,'Nodes','NODES','numnodes'),(18,'Segs','SEGS','numsegs'),(19,'Reject','REJECT','numsectors'),(20,'Things','THINGS','totalkills')]:
  old=f'    P_Load{name} (lumpnum+ML_{suffix});'
  extra=f'\n    doom_platform_mark({stage},{count},lumpnum,0);'
  if name=='SideDefs':extra+='\n    { unsigned h=2166136261u; for(i=0;i<numsides;i++){h=doom_checkpoint_mix(h,sides[i].toptexture);h=doom_checkpoint_mix(h,sides[i].midtexture);h=doom_checkpoint_mix(h,sides[i].bottomtexture);} doom_platform_mark(21,numsides,h,0); }'
  patch('p_setup.c',old,old+extra)
 patch('p_setup.c','    //printf ("free memory:', '    doom_platform_mark(22,numsectors,numsides,0);\n    //printf ("free memory:')
 patch('r_data.c','    texture = textures[texnum];\n\n    // Composited', '    texture = textures[texnum];\n    doom_platform_mark(100,texnum,texture->width,texture->patchcount);\n\n    // Composited')
 # Both lookup and composite have this exact call; record the selected patch.
 old='\trealpatch = W_CacheLumpNum (patch->patch, PU_CACHE);'
 # instrument.py caller supplies a count-aware helper separately for this pair.
 patch('r_data.c',old,'\tdoom_platform_mark(101,patch->patch,lumpinfo[patch->patch].position,lumpinfo[patch->patch].size);\n'+old,count=2)
 patch('r_data.c','    Z_Free(patchcount);','    Z_Free(patchcount);\n    doom_platform_mark(102,texnum,texturecompositesize[texnum],0);')
 patch('r_data.c','    texture = textures[texnum];\n\n    block =', '    texture = textures[texnum];\n    doom_platform_mark(99,texnum,texture->width,texture->patchcount);\n\n    block =')
 patch('r_data.c','    // Precalculate whatever possible.', '    doom_platform_mark(25,numtextures,totalwidth,0);\n    // Precalculate whatever possible.')
 patch('r_data.c','    GenerateTextureHashTable();','    GenerateTextureHashTable();\n    doom_platform_mark(26,numtextures,0,0);')
 patch('r_data.c','    if (demoplayback)\n\treturn;', '    doom_platform_mark(30,demoplayback,numtextures,numsides);\n    if (demoplayback)\n\treturn;')
 patch('r_data.c','    texturememory = 0;', '    doom_platform_mark(32,numtextures,doom_checkpoint_hash(texturepresent,numtextures),skytexture);\n    texturememory = 0;')
 patch('r_data.c','\t    texturememory += lumpinfo[lump].size;', '\t    doom_platform_mark(34,lump,lumpinfo[lump].position,lumpinfo[lump].size);\n\t    texturememory += lumpinfo[lump].size;')
 patch('r_data.c','    Z_Free(spritepresent);','    Z_Free(spritepresent);\n    doom_platform_mark(36,flatmemory,texturememory,spritememory);')

 patch('r_main.c','    R_SetupFrame (player);','    doom_platform_mark(37,player->mo->x,player->mo->y,player->mo->angle);\n    doom_platform_mark(38,player->viewz,player->extralight,0);\n    R_SetupFrame (player);\n    doom_platform_mark(40,viewx,viewy,viewangle);\n    doom_platform_mark(41,viewcos,viewsin,viewz);')
 for stage,call in [(42,'R_RenderBSPNode (numnodes-1);'),(43,'R_DrawPlanes ();'),(44,'R_DrawMasked ();')]:
  patch('r_main.c','    '+call,'    '+call+f'\n    doom_platform_mark({stage},0,0,0);')

 # Height inputs are recorded only for the player, not every spawned monster.
 for name,header in [('p_mobj.c','p_local.h'),('p_user.c','p_local.h'),('d_main.c','doomdef.h'),('i_video.c','doomgeneric.h')]:
  patch(name,'#include "'+header+'"','#include "'+header+'"\n#include "checkpoints.h"')
 patch('p_mobj.c','    mobj->thinker.function.acp1 = (actionf_p1)P_MobjThinker;',
  '    if(type==MT_PLAYER){\n'
  '      doom_platform_mark(63,mobj->subsector-subsectors,mobj->subsector->sector-sectors,z);\n'
  '      doom_platform_mark(64,mobj->z,mobj->floorz,mobj->ceilingz);\n'
  '      doom_platform_mark(65,x,y,mobj->subsector->sector->floorheight);\n'
  '    }\n    mobj->thinker.function.acp1 = (actionf_p1)P_MobjThinker;')
 patch('p_mobj.c','    mobj\t= P_SpawnMobj (x,y,z, MT_PLAYER);',
  '    doom_platform_mark(66,mthing->x,mthing->y,mthing->angle);\n    mobj\t= P_SpawnMobj (x,y,z, MT_PLAYER);')
 patch('p_mobj.c','    p->viewheight = VIEWHEIGHT;',
  '    p->viewheight = VIEWHEIGHT;\n    doom_platform_mark(67,p->viewheight,p->viewz,p->deltaviewheight);')
 patch('p_user.c','    // Regular movement bobbing',
  '    doom_platform_mark(70,player->mo->z,player->mo->floorz,player->mo->ceilingz);\n'
  '    doom_platform_mark(71,player->viewheight,player->deltaviewheight,player->bob);\n'
  '    doom_platform_mark(72,onground,player->cheats,player->playerstate);\n'
  '    // Regular movement bobbing')
 patch('p_user.c','    if ((player->cheats & CF_NOMOMENTUM) || !onground)',
  '    doom_platform_mark(73,player->bob,player->mo->momx,player->mo->momy);\n    if ((player->cheats & CF_NOMOMENTUM) || !onground)')
 patch('p_user.c','\tplayer->viewz = player->mo->z + player->viewheight;\n\treturn;',
  '\tplayer->viewz = player->mo->z + player->viewheight;\n\tdoom_platform_mark(74,player->viewz,player->mo->z,player->viewheight);\n\treturn;')
 patch('p_user.c','    player->viewz = player->mo->z + player->viewheight + bob;',
  '    doom_platform_mark(75,player->viewheight,bob,player->mo->z);\n    player->viewz = player->mo->z + player->viewheight + bob;')
 patch('p_user.c','\tplayer->viewz = player->mo->ceilingz-4*FRACUNIT;\n}',
  '\tplayer->viewz = player->mo->ceilingz-4*FRACUNIT;\n    doom_platform_mark(76,player->viewz,player->mo->ceilingz,player->deltaviewheight);\n}')
 # Fingerprint signed decoded sector heights, not native structure padding.
 patch('p_setup.c','    doom_platform_mark(13,numsectors,lumpnum,0);',
  '    doom_platform_mark(13,numsectors,lumpnum,0);\n'
  '    { unsigned h=2166136261u; for(i=0;i<numsectors;i++){h=doom_checkpoint_mix(h,sectors[i].floorheight);h=doom_checkpoint_mix(h,sectors[i].ceilingheight);} doom_platform_mark(27,numsectors,h,0); }')
 # Mark control-flow boundaries, never poll inside render loops or clock waits.
 patch('d_main.c','    redrawsbar = false;', '    doom_platform_mark(80,gamestate,wipegamestate,gametic);\n    redrawsbar = false;')
 patch('d_main.c','    if (gamestate == GS_LEVEL && gametic)\n    \tHU_Drawer ();',
  '    doom_platform_mark(81,0,0,0);\n    if (gamestate == GS_LEVEL && gametic)\n    \tHU_Drawer ();\n    doom_platform_mark(82,0,0,0);')
 patch('d_main.c','    // see if the border needs to be updated to the screen',
  '    doom_platform_mark(83,0,0,0);\n    // see if the border needs to be updated to the screen')
 patch('d_main.c','    if (testcontrols)\n    {\n        // Box', '    doom_platform_mark(84,0,0,0);\n    if (testcontrols)\n    {\n        // Box')
 patch('d_main.c','    M_Drawer ();          // menu is drawn even on top of everything',
  '    doom_platform_mark(85,0,0,0);\n    M_Drawer ();          // menu is drawn even on top of everything\n    doom_platform_mark(86,0,0,0);')
 patch('d_main.c','    // normal update','    doom_platform_mark(87,wipe,0,0);\n    // normal update')
 patch('d_main.c','    wipe_EndScreen(0, 0, SCREENWIDTH, SCREENHEIGHT);',
  '    doom_platform_mark(88,0,0,0);\n    wipe_EndScreen(0, 0, SCREENWIDTH, SCREENHEIGHT);\n    doom_platform_mark(89,0,0,0);')
 patch('d_main.c','    wipestart = I_GetTime () - 1;',
  '    wipestart = I_GetTime () - 1;\n    doom_platform_mark(90,wipestart,0,0);')
 patch('d_main.c','\twipestart = nowtime;',
  '\tdoom_platform_mark(91,nowtime,tics,wipestart);\n\twipestart = nowtime;')
 patch('d_main.c','\tdone = wipe_ScreenWipe(wipe_Melt',
  '\tdoom_platform_mark(92,tics,0,0);\n\tdone = wipe_ScreenWipe(wipe_Melt')
 patch('d_main.c','\t\t\t       , 0, 0, SCREENWIDTH, SCREENHEIGHT, tics);',
  '\t\t\t       , 0, 0, SCREENWIDTH, SCREENHEIGHT, tics);\n\tdoom_platform_mark(93,done,0,0);')
 patch('d_main.c','\tI_UpdateNoBlit ();','\tI_UpdateNoBlit ();\n\tdoom_platform_mark(94,0,0,0);')
 patch('d_main.c','\tI_FinishUpdate ();                      // page flip or blit buffer',
  '\tdoom_platform_mark(95,0,0,0);\n\tI_FinishUpdate ();                      // page flip or blit buffer')
 patch('i_video.c','    /* Offsets in case FB is bigger than DOOM */',
  '    doom_platform_mark(96,s_Fb.xres,s_Fb.yres,s_Fb.bits_per_pixel);\n    /* Offsets in case FB is bigger than DOOM */')
 patch('i_video.c','    /* DRAW SCREEN */','    doom_platform_mark(97,fb_scaling,x_offset,x_offset_end);\n    /* DRAW SCREEN */')
 patch('i_video.c','\tDG_DrawFrame();','\tdoom_platform_mark(98,0,0,0);\n\tDG_DrawFrame();')
