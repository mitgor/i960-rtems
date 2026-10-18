#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "player.h"
struct guarded {unsigned char before[32];struct c8_player p;unsigned char after[32];};
static unsigned word(const unsigned char*p){return p[0]|(unsigned)p[1]<<8|(unsigned)p[2]<<16|(unsigned)p[3]<<24;}
int main(void){
 static const unsigned char loop[]={0x70,0x01,0x12,0x00};
 static const unsigned char wait[]={0xf0,0x0a,0x12,0x00};
 struct guarded g;unsigned char out[512],reference[304];struct chip8 oracle;
 unsigned i,carry=0,executed,ticks,frames=0;
 memset(&g,0xa5,sizeof(g));assert(c8_player_init(&g.p,loop,sizeof(loop),1,500,0));c8_reset(&oracle,1);memcpy(oracle.ram+512,loop,sizeof(loop));
 /* Restart: every emitted reply is checked against the separate C8G1 core. */
 assert(c8_player_init(&g.p,loop,sizeof(loop),1,500,0));
 for(i=0;i<=6000;i++){
  unsigned ret;
  carry+=i?600:0;ticks=carry/1000;carry%=1000;
  c8_run(&oracle,i?5:0,ticks,0,&executed);
  ret=c8_player_update(&g.p,i*10,out);
  if(ret){assert(ret==1);frames++;{unsigned char query[24]={0x43,0x38,0x47,0x31,1};assert(!c8_request(&oracle,query,24,reference,304));reference[8]=executed;}assert(!memcmp(reference,out,304));assert(word(out+312)==frames);}
 }
 assert(g.p.guest.total==30000 && frames==3601);
 for(i=0;i<32;i++)assert(g.before[i]==0xa5&&g.after[i]==0xa5);
 assert(c8_player_init(&g.p,wait,sizeof(wait),1,500,0));
 assert(c8_player_key(&g.p,3|256)&&c8_player_key(&g.p,3));
 assert(c8_player_update(&g.p,0,out)==1);assert(g.p.pressed==8);
 c8_player_update(&g.p,10,out);assert(g.p.guest.v[0]==3&&g.p.held==0&&g.p.pressed==0);
 {struct c8_player before=g.p;assert(!c8_player_key(&g.p,512)&&!c8_player_key(&g.p,16));assert(!memcmp(&before,&g.p,sizeof(before)));}
 assert(c8_player_init(&g.p,loop,sizeof(loop),1,4000,0xfffffff5u));
 c8_player_update(&g.p,9,out);assert(g.p.guest.total==80);
 c8_player_update(&g.p,10009,out);assert(g.p.guest.total==1080&&g.p.dropped_ms==9750);
 assert(!c8_player_init(&g.p,loop,1,1,500,0));assert(!c8_player_init(&g.p,loop,4,1,4001,0));
 puts("PASS real-time player: 6001 oracle slices/3601 frames, guards, brief keys, rejection, clock wrap, bounded catch-up");return 0;
}
