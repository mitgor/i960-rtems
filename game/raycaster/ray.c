#include "ray.h"
#include "trig.h"
#include <stddef.h>
/* Resolved to the existing RTEMS helpers on the target; host libc for oracle. */
extern void *memcpy(void*,const void*,size_t);
extern void *memmove(void*,const void*,size_t);
extern void *memset(void*,int,size_t);
extern int memcmp(const void*,const void*,size_t);
extern size_t strlen(const char*);
static const unsigned char world[12][13]={
 "111111111111","100000000001","100000000001","100022000001",
 "100020000001","100020000001","100000003001","100000003001",
 "100440000001","100000000001","100000000001","111111111111"};
struct ray {
 int x,y;unsigned int angle,column,frame,steps,hash,digest;
 unsigned char front[RAY_PIXELS],back[RAY_PIXELS];
 unsigned char a[4112] __attribute__((aligned(16)));
 unsigned char b[4112] __attribute__((aligned(16)));
};
unsigned int ray_size(void){return sizeof(struct ray);}
static unsigned int word(const unsigned char*p){return (unsigned int)p[0]|(unsigned int)p[1]<<8|(unsigned int)p[2]<<16|(unsigned int)p[3]<<24;}
static void put(unsigned char*p,unsigned int n){p[0]=n;p[1]=n>>8;p[2]=n>>16;p[3]=n>>24;}
static unsigned int hash(const unsigned char*p,unsigned int n){unsigned int h=2166136261u;while(n--)h=(h^*p++)*16777619u;return h;}
static int wall(int x,int y){if(x<0||x>=12||y<0||y>=12)return 1;return world[y][x]-'0';}
static int space(int x,int y){return !wall((x-128)/1024,(y-128)/1024)&&!wall((x+128)/1024,(y-128)/1024)&&!wall((x-128)/1024,(y+128)/1024)&&!wall((x+128)/1024,(y+128)/1024);}
static void move(struct ray*s,unsigned int keys){int dx,dy,sign;
 if(keys&4)s->angle=(s->angle+252)&255;
 if(keys&8)s->angle=(s->angle+4)&255;
 sign=((keys&1)!=0)-((keys&2)!=0);
 dx=cosine[s->angle]*sign/16;dy=cosine[(s->angle+192)&255]*sign/16;
 if(space(s->x+dx,s->y))s->x+=dx;
 if(space(s->x,s->y+dy))s->y+=dy;
}
static void column(struct ray*s,unsigned int col){
 int dirx=cosine[s->angle],diry=cosine[(s->angle+192)&255];
 int camera=((int)col*2+1)*1024/RAY_W-1024;
 int rx=dirx-diry*camera*169/262144,ry=diry+dirx*camera*169/262144;
 int mx=s->x/1024,my=s->y/1024,sx=rx<0?-1:1,sy=ry<0?-1:1;
 unsigned int ax=rx<0?-rx:rx,ay=ry<0?-ry:ry;
 unsigned int deltax=ax?1048576u/ax:0x4000000u,deltay=ay?1048576u/ay:0x4000000u;
 unsigned int tx=ax?(unsigned int)(sx<0?s->x%1024:1024-s->x%1024)*1024/ax:0x4000000u;
 unsigned int ty=ay?(unsigned int)(sy<0?s->y%1024:1024-s->y%1024)*1024/ay:0x4000000u;
 unsigned int step,side=0,dist=1024,height,y;int material=1,top,bottom;
 for(step=0;step<32;step++){
  if(tx<ty){dist=tx;tx+=deltax;mx+=sx;side=0;}else{dist=ty;ty+=deltay;my+=sy;side=1;}
  material=wall(mx,my);if(material)break;
 }
 s->steps+=step+1;
 if(!dist)dist=1;
 height=RAY_H*1024u/dist;if(height>RAY_H*4)height=RAY_H*4;
 top=(RAY_H-(int)height)/2;bottom=top+(int)height;
 for(y=0;y<RAY_H;y++)s->back[y*RAY_W+col]=(int)y<top?0:((int)y>=bottom?1:2+(material-1)*2+side);
}
static void bench(struct ray*s,unsigned int kind,unsigned int reps){unsigned int i,j,result=0;
 for(i=0;i<4112;i++){s->a[i]=(unsigned char)(i*17+3);s->b[i]=0;}
 s->a[4095]=0;
 /* strlen input has no earlier zero. */
 if(kind==6)for(i=0;i<4095;i++)s->a[i]='x';
 if(kind==5)memcpy(s->b,s->a,4096);
 for(j=0;j<reps;j++){
  switch(kind){
  case 0:break;
  case 1:memcpy(s->b,s->a,4096);break;
  case 2:memcpy(s->b+1,s->a+1,4096);break;
  case 3:memset(s->b,(int)(j&255),4096);break;
  case 4:memmove(s->a+1,s->a,4096);break;
  case 5:result+=(memcmp(s->a,s->b,4096)==0);break;
  case 6:result+=(unsigned int)strlen((char*)s->a);break;
  case 7:case 8:result++;break; /* Target adapter performs these RTEMS operations. */
  }
 }
 s->digest=hash(s->a,sizeof(s->a))^hash(s->b,sizeof(s->b))^result;
}
unsigned int ray_request(void*state,const unsigned char*in,unsigned int n,unsigned char*out,unsigned int capacity){
 struct ray*s=(struct ray*)state;unsigned int op,budget,keys,pixels,kind,reps,i,limit;
 if(n!=32||word(in)!=RAY_MAGIC||word(in+28))return 1;
 op=word(in+4);budget=word(in+8);keys=word(in+12);pixels=word(in+16);kind=word(in+20);reps=word(in+24);
 if(op>3||pixels>1||keys>15||budget>80||kind>8||reps>128)return 1;
 if((op!=1&&(budget||keys))||(op==1&&!budget)||(op!=3&&(kind||reps))||(op==3&&!reps))return 1;
 if(capacity<(pixels?RAY_REPLY:RAY_HEADER))return 2;
 if(op==0){s->x=2560;s->y=2560;s->angle=0;s->column=80;s->frame=0;s->steps=0;s->digest=0;for(i=0;i<RAY_PIXELS;i++)s->front[i]=0;s->hash=hash(s->front,RAY_PIXELS);}
 else if(op==1){
  if(s->column==80){s->column=0;s->steps=0;move(s,keys);}
  limit=s->column+budget;if(limit>80)limit=80;
  while(s->column<limit){column(s,s->column);s->column++;}
  if(s->column==80){memcpy(s->front,s->back,RAY_PIXELS);s->frame++;s->hash=hash(s->front,RAY_PIXELS);}
 }else if(op==3)bench(s,kind,reps);
 for(i=0;i<RAY_HEADER;i++)out[i]=0;
 put(out,RAY_MAGIC);put(out+4,s->frame);put(out+8,s->column);put(out+12,s->x);put(out+16,s->y);put(out+20,s->angle);
 put(out+24,s->steps);put(out+28,s->hash);put(out+32,s->digest);put(out+36,pixels?RAY_PIXELS:0);put(out+40,kind);put(out+44,reps);
 if(pixels)memcpy(out+RAY_HEADER,s->front,RAY_PIXELS);
 return 0;
}
