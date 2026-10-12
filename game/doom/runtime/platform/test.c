/* Linked only against the private Newlib/port for tested libc symbols. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <math.h>
#include <errno.h>
#include <sys/stat.h>
#include <fcntl.h>
#include "platform.h"
#include "../heap.h"
#include "i_video.h"
#define CHECK(x) do{if(!(x))return __LINE__;}while(0)
static unsigned char storage[8*1048576] __attribute__((aligned(16))),wad[4096],pixels[64000],rgb[768],copy[64000];
unsigned char *DG_ScreenBuffer=pixels;
struct color colors[256];
static struct arena arena;static struct doom_heap heap;static unsigned lock,ticks,reads,fail_read;
static int enter(void*p){(void)p;if(lock)return 0;lock=1;return 1;}static void leave(void*p){(void)p;lock=0;}static int progress(void*p){(void)p;return 1;}
static void*allocate(unsigned n){return doom_heap_malloc(&heap,n);}static void release(void*p){if(!doom_heap_free(&heap,p))__builtin_trap();}
static unsigned clock_ms(void){return ticks++;}
static int read_wad(unsigned id,unsigned off,void*dst,unsigned n){unsigned token,i;if(id!=1||off>sizeof(wad)||n>512)return -1;token=doom_heap_borrow(&heap,dst,n);if(!token)return -1;reads++;
 if(n>sizeof(wad)-off)n=sizeof(wad)-off;for(i=0;i<n;i++)((unsigned char*)dst)[i]=wad[off+i];if(!doom_heap_return(&heap,dst,token))__builtin_trap();return fail_read?-2:(int)n;}
static void exit_seven(void){exit(7);}
void DG_Init(void);void DG_DrawFrame(void);void DG_SleepMs(unsigned);unsigned DG_GetTicksMs(void);int DG_GetKey(int*,unsigned char*);void DG_SetWindowTitle(const char*);
int main(void){struct doom_runtime_v1 a={0};struct doom_heap_hooks hooks={enter,leave,progress,0};unsigned i,n,before;char s[256],text[4096],*p,*q;FILE*f,*g;int value,pressed;long long count=-1;unsigned char key;double d;
 CHECK(arena_init(&arena,storage,sizeof storage)&&doom_heap_init(&heap,&arena,&hooks));
 for(i=0;i<sizeof(wad);i++)wad[i]=i%251;for(i=0;i<64000;i++)pixels[i]=i%239;for(i=0;i<256;i++){colors[i].r=i;colors[i].g=255-i;colors[i].b=i^85;}
 a.magic=DOOM_API_MAGIC;a.version=DOOM_API_VERSION;a.bytes=sizeof(a);a.features=DOOM_API_FEATURES;a.pointer_bytes=sizeof(void*);a.little_endian=1;a.arena_bytes=sizeof storage;a.max_read=512;a.file_id=1;a.file_bytes=sizeof(wad);a.allocate=allocate;a.release=release;a.read=read_wad;a.ticks_ms=clock_ms;
 {struct doom_runtime_v1 bad=a;bad.little_endian=0;CHECK(!doom_platform_bind(&bad,"/iwad.wad"));bad=a;bad.reserved[0]=1;CHECK(!doom_platform_bind(&bad,"/iwad.wad"));}
 CHECK(doom_platform_bind(&a,"/iwad.wad")&&!doom_platform_bind(&a,"/iwad.wad"));
 p=malloc(16);CHECK(p);memset(p,0x5a,16);q=realloc(p,32);CHECK(q&&q[0]==0x5a&&q[15]==0x5a);p=q;
 CHECK(!realloc(p,0xffffffffu)&&p[0]==0x5a);free(p);CHECK(!calloc(0xffffffffu,2));p=calloc(128,3);CHECK(p);for(i=0;i<384;i++)CHECK(!p[i]);free(p);
 p=strdup("immutable");CHECK(p&&!strcmp(p,"immutable")&&!doom_platform_finish());free(p);
 CHECK(!strcmp(strstr("old i960 new","i960"),"i960 new")&&!strcasecmp("Mylex","MYLEX")&&!strncasecmp("ROM","rom!",3));
 CHECK(atoi(" -29")==-29&&atof("1.25")==1.25&&fabs(-1.5)==1.5);
 CHECK(snprintf(s,sizeof s,"%s %d %u %08x %lld %.3f", "i960",-29,42u,0xab,1234567890123ll,1.25)==40);CHECK(!strcmp(s,"i960 -29 42 000000ab 1234567890123 1.250"));
 CHECK(snprintf(s,5,"abcdef")==6&&!strcmp(s,"abcd"));CHECK(snprintf(0,0,"abcdef")==6);
 CHECK(snprintf(s,sizeof s,"abc%lln-end",&count)==7&&count==3&&!strcmp(s,"abc-end"));
 CHECK(sscanf(" -29 1.25 ROM","%d %lf %3s",&value,&d,s)==3&&value==-29&&d==1.25&&!strcmp(s,"ROM"));
 CHECK(!fopen("/config.cfg","rb")&&errno==ENOENT);CHECK(!fopen("/iwad.wad","wb")&&errno==EROFS);
 f=fopen("/iwad.wad","rb");CHECK(f);CHECK(fread(s,1,100,f)==100&&!memcmp(s,wad,100));before=reads;
 CHECK(!fseek(f,0,SEEK_SET)&&ftell(f)==0&&fread(s,1,100,f)==100&&!memcmp(s,wad,100)&&reads==before);
 CHECK(!fseek(f,-37,SEEK_END)&&ftell(f)==4096-37&&fread(s,1,100,f)==37&&!memcmp(s,wad+4096-37,37));CHECK(fread(s,1,100,f)==0&&feof(f));
 CHECK(!fclose(f));g=fopen("/iwad.wad","rb");CHECK(g);fail_read=1;CHECK(fread(s,1,32,g)==0&&ferror(g));fail_read=0;CHECK(!fclose(g));
 CHECK(mkdir("/save",0700)==-1&&errno==EROFS&&remove("/iwad.wad")==-1&&errno==EROFS&&rename("/iwad.wad","/other")==-1&&errno==EROFS&&system("sh")==-1&&errno==ENOSYS);
 CHECK(printf("Doom on i960 %d\n",29)==16);CHECK(!fflush(stdout));n=doom_platform_log(text,sizeof text);CHECK(n==16&&!memcmp(text,"Doom on i960 29\n",16));
 memset(text,'x',sizeof text);CHECK(fwrite(text,1,sizeof text,stdout)==sizeof text);CHECK(!fflush(stdout));CHECK(puts("end")>=0);CHECK(!fflush(stdout));CHECK(doom_platform_stats()->log_dropped>0);CHECK(doom_platform_log(text,sizeof text)==sizeof text);
 DG_Init();DG_SetWindowTitle("Doom");DG_DrawFrame();CHECK(doom_platform_stats()->frames==1&&doom_platform_frame(copy,sizeof copy,rgb,sizeof rgb)&&!memcmp(copy,pixels,sizeof copy));for(i=0;i<256;i++)CHECK(rgb[3*i]==i&&rgb[3*i+1]==255-i&&rgb[3*i+2]==(i^85));
 CHECK(!DG_GetKey(&pressed,&key));for(i=0;i<32;i++)CHECK(doom_platform_key(i&1,(unsigned char)i));CHECK(!doom_platform_key(1,42));for(i=0;i<32;i++){CHECK(DG_GetKey(&pressed,&key)&&pressed==(int)(i&1)&&key==i);}CHECK(!DG_GetKey(&pressed,&key));
 before=DG_GetTicksMs();DG_SleepMs(35);CHECK(DG_GetTicksMs()-before>=35);CHECK(doom_platform_call(exit_seven)==7&&doom_platform_stats()->exited);
 CHECK(doom_platform_finish()&&!heap.blocks&&!doom_platform_stats()->blocks&&!doom_platform_finish());CHECK(doom_heap_stop(&heap)&&doom_heap_drain(&heap));
 return 0;
}
