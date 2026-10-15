/* Exact packed-coordinate spans. Unaligned destinations use byte stores.
 * No access beyond count pixels; source/map remain caller-owned read-only. */
#ifndef DOOM_RENDER_SPAN_H
#define DOOM_RENDER_SPAN_H
static void doom_span(unsigned char *dst,const unsigned char *src,
 const unsigned char *map,unsigned pos,unsigned step,unsigned count,unsigned low)
{
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
