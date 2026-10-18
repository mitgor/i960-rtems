#include "player.h"
static void put(unsigned char*p,unsigned v){p[0]=v;p[1]=v>>8;p[2]=v>>16;p[3]=v>>24;}
unsigned c8_player_size(void){return sizeof(struct c8_player);}
unsigned c8_player_init(struct c8_player*p,const unsigned char*rom,unsigned n,unsigned seed,unsigned hz,unsigned now){
 unsigned i;unsigned char*b=(unsigned char*)p;
 if(n<2||n>3584||hz<1||hz>4000)return 0;
 for(i=0;i<sizeof(*p);i++)b[i]=0;
 c8_reset(&p->guest,seed);
 for(i=0;i<n;i++)p->guest.ram[512+i]=rom[i];
 p->hz=hz;p->last=now;p->start=now;p->frame_carry=1000;return 1;
}
unsigned c8_player_key(struct c8_player*p,unsigned event){unsigned key=event&255u;
 if(event>511u||key>15u)return 0;
 if(event&256u){p->held|=1u<<key;p->pressed|=1u<<key;}
 else p->held&=~(1u<<key);
 p->input_seen++;return 1;
}
unsigned c8_player_update(struct c8_player*p,unsigned now,unsigned char*out){
 unsigned elapsed=now-p->last,cycles,ticks,i,j;
 if(p->updates>=0xfffffffdu)return 2;
 if(p->trace_count>=8u)return 3;
 p->last=now;
 if(elapsed>250u){p->dropped_ms+=elapsed-250u;elapsed=250u;}
 p->cycle_carry+=elapsed*p->hz;p->tick_carry+=elapsed*60u;p->frame_carry+=elapsed*60u;
 cycles=p->cycle_carry/1000u;p->cycle_carry%=1000u;
 ticks=p->tick_carry/1000u;p->tick_carry%=1000u;
 i=p->trace_count++;p->updates++;
 p->trace[i][0]=cycles;p->trace[i][1]=p->held|p->pressed;p->trace[i][2]=ticks;p->trace[i][3]=p->input_seen;
 p->status=c8_run(&p->guest,cycles,ticks,p->held|p->pressed,&p->executed);
 if(cycles)p->pressed=0;
 if(p->frame_carry<1000u)return 0;
 p->frame_carry%=1000u;
 if(p->generation>=0xfffffffdu)return 2;
 p->generation++;
 for(i=0;i<C8_PACKET_BYTES;i++)out[i]=0;
 put(out,C8_MAGIC);put(out+4,p->status);put(out+8,p->executed);put(out+12,p->guest.total);
 put(out+16,p->guest.pc);put(out+20,p->guest.index);put(out+24,p->guest.delay);put(out+28,p->guest.sound);
 for(i=0;i<16;i++)out[32+i]=p->guest.v[i];
 for(i=0;i<256;i++)out[48+i]=p->guest.frame[i];
 put(out+304,C8_PLAYER_MAGIC);put(out+308,1);put(out+312,p->generation);
 put(out+316,p->held);put(out+320,p->input_seen);put(out+324,p->hz);
 put(out+328,now);put(out+332,p->dropped_ms);
 put(out+336,p->trace_count);put(out+340,p->updates);put(out+344,p->start);
 for(i=0;i<p->trace_count;i++)for(j=0;j<4;j++)put(out+352+i*16+j*4,p->trace[i][j]);
 p->trace_count=0;
 return 1;
}
