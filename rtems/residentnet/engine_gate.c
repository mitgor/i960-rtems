/* Exact-build admission. Host-selected CRCs are transport checks, never trust.
 * A compiled SHA identity authenticates both image and ordered R_960_32 sites.
 * This unit is placed in a separately protected code window. */
#ifdef I960_DOOM_ENGINE
#include "upload.h"
#include "../../loader/segmented/image.h"
#include "../../loader/digest/sha256.h"
#include "doom_runtime.h"
#include "doom_heap_shared.h"
#include "engine_identity.h"
extern void exclusive_abort(void);
#ifndef ENGINE_GATE_NATIVE
extern unsigned upload_stopping(void);
#endif
static unsigned results[12];
static unsigned word(const unsigned char*p){return (unsigned)p[0]|((unsigned)p[1]<<8)|((unsigned)p[2]<<16)|((unsigned)p[3]<<24);}
static void store(unsigned char*p,unsigned v){unsigned i;for(i=0;i<4;i++)p[i]=(unsigned char)(v>>(8*i));}
static int digest(struct seg_image*s,unsigned off,unsigned n,const unsigned char*expected,int yielding){struct sha256 h;unsigned char out[32];unsigned i,k;sha256_init(&h);
 while(n){k=n>1024?1024:n;if(!sha256_update(&h,s->base+off,k))return 0;off+=k;n-=k;if(yielding){doom_shared_yield();if(upload_stopping())return 0;}}
 sha256_finish(&h,out);for(i=0;i<32;i++)if(out[i]!=expected[i])return 0;return 1;
}
unsigned engine_report(unsigned i){return i<12?results[i]:~0u;}
unsigned engine_run(struct seg_image*s,int(*sync)(void*,unsigned),unsigned*value){unsigned i,j,x,last=0,base=(unsigned)(unsigned long)s->base,ok;void*entry;const struct doom_runtime_owned*a;
#ifdef ENGINE_STARTUP
#ifndef I960_WAD_BATCH
#error startup needs validated batch runtime
#endif
 a=doom_runtime_owned_batch_api();
#else
 a=doom_runtime_owned_api();
#endif
 if(!a||s->state!=SEG_READY||s->manifest.count!=4||s->manifest.entry!=ENGINE_ENTRY)return 1;
 for(i=0;i<4;i++){const struct segment*p=s->manifest.segment+i;const unsigned*g=engine_geometry[i];if(p->offset!=g[0]||p->file_bytes!=g[1]||p->memory_bytes!=g[2]||p->flags!=g[3])return 1;}
 /* The canonical alignment gaps are not file segments. Require and clear them
  * explicitly so stale arena bytes cannot participate in the identity. */
 for(i=0;i<3;i++){unsigned end=engine_geometry[i][0]+engine_geometry[i][2],next=engine_geometry[i+1][0];for(j=end;j<next;j++)s->base[j]=0;}
 if(!digest(s,0,ENGINE_FILE,engine_image_sha,1)||!digest(s,ENGINE_META,ENGINE_SITES*4,engine_metadata_sha,1))return 2;
 for(i=0;i<ENGINE_SITES;i++){x=word(s->base+ENGINE_META+4*i);if((x&3)||x>ENGINE_FILE-4||(i&&x<=last)||word(s->base+x)>ENGINE_SPAN)return 2;last=x;}
 for(i=0;i<engine_geometry[2][2];i++){if(s->base[engine_geometry[2][0]+i])return 2;if(!(i&1023)){doom_shared_yield();if(upload_stopping())return 2;}}
 if(!doom_shared_enter((void*)1))return 3;entry=seg_start(s);doom_shared_leave((void*)1);if(!entry)return 4;
 /* Once RUNNING, uncertainty retains the whole image until a reboot. */
 for(i=0;i<ENGINE_SITES;i++){x=word(s->base+ENGINE_META+4*i);store(s->base+x,word(s->base+x)+base);if(!(i&255))doom_shared_yield();}
 if(!sync(s->base,ENGINE_TEXT)||!doom_runtime_owned_begin())goto uncertain;
 #ifdef ENGINE_GATE_NATIVE
 {extern unsigned engine_native_call(struct seg_image*,const struct doom_runtime_owned*);*value=engine_native_call(s,a);}
#else
 *value=((unsigned(*)(const struct doom_runtime_owned*))entry)(a);
#endif
 for(i=0;i<12;i++)results[i]=word(s->base+ENGINE_RESULT+4*i);
#ifdef ENGINE_STARTUP
 if((*value!=0x454e4700u&&*value!=0x454e4702u)||results[0]!=0x454e4750u||results[1]!=2||results[10]!=1)goto uncertain;
 if(*value==0x454e4700u&&(results[2]!=6291456u||results[3]!=ENGINE_FRAME||results[4]!=ENGINE_PALETTE||results[5]!=1||results[6]!=1||results[9]||results[11]!=213))goto uncertain;
 if(*value==0x454e4702u&&(results[9]<2||results[9]>4||results[5]||results[6]))goto uncertain;
#else
 if((*value!=0x454e4700u&&*value!=0x454e4702u)||results[0]!=0x454e4750u||results[1]!=1||results[10]!=1||results[11]||results[9]>3)goto uncertain;
 if(*value==0x454e4700u&&(results[2]!=6291456u||!results[5]||!results[6]||results[9]))goto uncertain;
 if(*value==0x454e4702u&&results[9]!=2)goto uncertain;
#endif
 if(!doom_runtime_owned_end())goto uncertain;
 if(!digest(s,ENGINE_META,ENGINE_SITES*4,engine_metadata_sha,0))goto uncertain;
 /* Executable bytes are immutable. Undo only their authenticated relocations
  * for an independent canonical digest; mutable data is discarded on cancel. */
 for(i=0;i<ENGINE_SITES;i++){x=word(s->base+ENGINE_META+4*i);if(x<ENGINE_TEXT){unsigned v=word(s->base+x);if(v<base||v-base>ENGINE_SPAN)goto uncertain;store(s->base+x,v-base);}}
 if(!digest(s,0,ENGINE_TEXT,engine_text_sha,0)||!sync(s->base,ENGINE_TEXT))goto uncertain;
 /* One-shot lifetime: the engine's libc state is retired, never reused. */
 if(!doom_shared_enter((void*)1))goto uncertain;ok=seg_cancel(s)&&seg_complete(s);doom_shared_leave((void*)1);return ok?0:12;
 uncertain:seg_uncertain(s);exclusive_abort();return 7;
}
#endif
