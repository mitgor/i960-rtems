/* Exact packed-coordinate spans. Unaligned destinations use byte stores.
 * No access beyond count pixels; source/map remain caller-owned read-only. */
#ifndef DOOM_RENDER_SPAN_H
#define DOOM_RENDER_SPAN_H
static void doom_span(unsigned char *dst,const unsigned char *src,
 const unsigned char *map,unsigned pos,unsigned step,unsigned count,unsigned low)
{
#ifdef DOOM_SPAN_FOUR
 while(count>=4){
  unsigned p1=pos+step,p2=p1+step,p3=p2+step;
  unsigned a=map[src[(pos>>26)|((pos>>4)&4032u)]];
  unsigned b=map[src[(p1>>26)|((p1>>4)&4032u)]];
  unsigned c=map[src[(p2>>26)|((p2>>4)&4032u)]];
  unsigned d=map[src[(p3>>26)|((p3>>4)&4032u)]];
  if(low){
   if(!((unsigned long)dst&3u)){
    *(unsigned*)dst=a*0x101u|b*0x1010000u;
    *(unsigned*)(dst+4)=c*0x101u|d*0x1010000u;
   }else {dst[0]=a;dst[1]=a;dst[2]=b;dst[3]=b;
          dst[4]=c;dst[5]=c;dst[6]=d;dst[7]=d;}
   dst+=8;
  }else {
   if(!((unsigned long)dst&3u))*(unsigned*)dst=a|(b<<8)|(c<<16)|(d<<24);
   else {dst[0]=a;dst[1]=b;dst[2]=c;dst[3]=d;}
   dst+=4;
  }
  pos=p3+step;count-=4;
 }
#endif
 while(count>=2){
  unsigned p1=pos+step;
  unsigned a=map[src[(pos>>26)|((pos>>4)&4032u)]];
  unsigned b=map[src[(p1>>26)|((p1>>4)&4032u)]];
  if(low){
   if(!((unsigned long)dst&3u))*(unsigned*)dst=a*0x101u|b*0x1010000u;
   else {dst[0]=a;dst[1]=a;dst[2]=b;dst[3]=b;}
   dst+=4;
  }else {dst[0]=a;dst[1]=b;dst+=2;}
  pos=p1+step;count-=2;
 }
 if(count){unsigned a=map[src[(pos>>26)|((pos>>4)&4032u)]];dst[0]=a;if(low)dst[1]=a;}
}
#endif
