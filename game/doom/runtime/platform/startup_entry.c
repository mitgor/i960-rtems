/* One-shot actual Doom startup, exits at the first presented frame. */
#include "platform.h"
#include "doomgeneric.h"
#include "z_zone.h"
extern int doom_wad_backend_bind(const struct doom_runtime_v1*,const char*);
extern int doom_wad_backend_close(void);
volatile unsigned doom_engine_result[12];
extern void doom_platform_mark(unsigned,unsigned,unsigned,unsigned);
static void start(void){
#ifdef DOOM_PLAY
 char *argv[]={"doom","-iwad","/iwad.wad","-mb","6","-nosound","-warp","1","1","-skill","3","-config","/no-config","-extraconfig","/no-extra"};
#else
 char *argv[]={"doom","-iwad","/iwad.wad","-mb","6","-nosound","-timedemo","demo1","-config","/no-config","-extraconfig","/no-extra"};
#endif
#ifdef DOOM_COLUMN_TEST
 {extern int doom_column_selftest(void);extern void abort(void);
 if(!doom_column_selftest())abort();}
#endif
 doom_platform_mark(2,0,0,0);
 doomgeneric_Create(sizeof(argv)/sizeof(*argv),argv);
 doom_platform_mark(3,0,0,0);
 for(;;){DG_SleepMs(29);doomgeneric_Tick();}
}
unsigned doom_engine_entry(const struct doom_runtime_owned*a){int rc;const struct doom_platform_stats*s;
 if(!a||a->io.version!=DOOM_API_BATCH_VERSION||!doom_platform_bind_owned(a,"/iwad.wad")||!doom_wad_backend_bind(&a->io,"/iwad.wad"))return 1;
 doom_platform_mark(1,0,0,0);
 doom_engine_result[0]=0x454e4750u;doom_engine_result[1]=2;
#ifdef DOOM_PERSISTENT_PLAY
 doom_platform_startup(0u); /* Card owner supplies heartbeat and STOP bounds. */
#else
 doom_platform_startup(1800000u);
#endif
 rc=doom_platform_call(start);s=doom_platform_stats();doom_platform_mark(61,rc,0,0);
 doom_engine_result[2]=6291456u;doom_engine_result[3]=s->frame_hash;doom_engine_result[4]=s->palette_hash;doom_engine_result[5]=s->frames;doom_engine_result[6]=rc==213;
 doom_engine_result[7]=s->peak_bytes;doom_engine_result[8]=s->peak_blocks;doom_engine_result[9]=rc==213?0:rc==210?2:rc==212?4:3;doom_engine_result[11]=rc;
 if(!doom_wad_backend_close()||!doom_platform_retire())return 5;
 doom_platform_mark(62,0,0,0);
 doom_engine_result[10]=1;return rc==213?0x454e4700u:0x454e4702u;
}
