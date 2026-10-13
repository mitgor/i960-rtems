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
