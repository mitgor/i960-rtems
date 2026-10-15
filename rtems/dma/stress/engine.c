/* Deterministic DMA exerciser, not Doom. Exact-image admission and the actual
 * pinned-frame service are shared; no WAD, libc or renderer initialization. */
#include "../../../game/doom/runtime/startup/checkpoint_api.h"
volatile unsigned doom_engine_result[12];
unsigned char doom_platform_frames[2][65536];
unsigned stress_identity=0x31534644;
unsigned doom_engine_entry(const struct doom_runtime_owned *a){
 const struct doom_runtime_checkpoint *c=(const void*)a;
 unsigned g,i,slot;volatile unsigned delay;
 if(!a||a->magic!=DOOM_OWNED_MAGIC||a->version!=DOOM_CHECKPOINT_VERSION||a->bytes!=sizeof(*c)||!a->owner()||!c->mark)return 1;
 doom_engine_result[0]=0x454e4750;doom_engine_result[1]=3;doom_engine_result[2]=65536;
 for(g=1;g<=4096;g++){
  if(a->stopping())break;
#ifdef PP_PRODUCER
  slot=(g-1)&1;
#else
  slot=0;
#endif
  for(i=0;i<65536;i++)doom_platform_frames[slot][i]=(unsigned char)((i*13u)^(i>>8)^(g*37u));
  /* Vary interrupt phase without changing the DMA worker or its poll bound. */
  for(delay=0;delay<(g&127u)*31u;delay++){}
  if(c->mark(100,(unsigned)doom_platform_frames[slot],65536,g)<0)break;
  doom_engine_result[5]=g;
 }
 if(!a->stopping())return 2;
 doom_engine_result[9]=2;doom_engine_result[10]=1;doom_engine_result[11]=210;
 return 0x454e4702;
}
