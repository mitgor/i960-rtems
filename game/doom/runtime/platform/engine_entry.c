/* Full engine-linked preflight entry. No game initialization is implied by its
 * successful diagnostic status. Only this exact entry is admitted initially. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "platform.h"
#include "w_file.h"
#include "doomgeneric.h"
#include "i_video.h"
extern int doom_wad_backend_bind(const struct doom_runtime_v1*,const char*);
extern int doom_wad_backend_close(void);
extern wad_file_class_t stdc_wad_file;
volatile unsigned doom_engine_result[12];
unsigned doom_engine_entry(const struct doom_runtime_owned*a){unsigned i,j,code=3;unsigned char*zone=0,*pixels=0,*scratch=0;wad_file_t*f=0;char text[80];long long count=-1;
 if(!a||!a->owner||!a->owner()||!doom_platform_bind_owned(a,"/iwad.wad")||!doom_wad_backend_bind(&a->io,"/iwad.wad"))return 1;
 if(snprintf(text,sizeof text,"i960 %lld %.2f%lln",1234567890123ll,1.25,&count)!=23||count!=23||strcmp(text,"i960 1234567890123 1.25"))goto done;
 doom_engine_result[0]=0x454e4750u;doom_engine_result[1]=1;
 zone=malloc(6u*1048576u);if(!zone)goto done;
 for(i=0;i<6u*1048576u;i+=1024){if(doom_platform_checkpoint()){code=2;goto done;}for(j=0;j<1024;j++)zone[i+j]=0;}
 for(i=0;i<6u*1048576u;i+=1024){if(doom_platform_checkpoint()){code=2;goto done;}for(j=0;j<1024;j++)if(zone[i+j])goto done;}
 doom_engine_result[2]=6u*1048576u;
 pixels=malloc(64000);scratch=malloc(1024);if(!pixels||!scratch)goto done;
 for(i=0;i<64000;i++)pixels[i]=(unsigned char)(i%239);
 for(i=0;i<256;i++){colors[i].r=i;colors[i].g=255-i;colors[i].b=i^85;}
 DG_ScreenBuffer=pixels;DG_Init();DG_DrawFrame();doom_engine_result[3]=doom_platform_stats()->frame_hash;doom_engine_result[4]=doom_platform_stats()->palette_hash;
 f=stdc_wad_file.OpenFile("/iwad.wad");if(!f||stdc_wad_file.Read(f,0,scratch+7,12)!=12||memcmp(scratch+7,"IWAD",4)){code=doom_platform_checkpoint()==1?2:3;goto done;}doom_engine_result[5]=1;
 for(i=0;i<100;i++){if(doom_platform_checkpoint()){code=2;goto done;}if(a->wait_ms(10)){code=2;goto done;}}
 doom_engine_result[6]=1;code=0;
 done:
 if(f){stdc_wad_file.CloseFile(f);f=0;}if(!doom_wad_backend_close())return 4;
 DG_ScreenBuffer=0;free(scratch);free(pixels);free(zone);
 {const struct doom_platform_stats*s=doom_platform_stats();doom_engine_result[7]=s->peak_bytes;doom_engine_result[8]=s->peak_blocks;doom_engine_result[9]=code;}
 if(!doom_platform_finish())return 5;doom_engine_result[10]=1;
 return doom_engine_result[0]==0x454e4750u?(code?0x454e4702u:0x454e4700u):6;
}
