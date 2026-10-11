#include "chip8.h"
static const c8_u8 font[80]={
 0xf0,0x90,0x90,0x90,0xf0,0x20,0x60,0x20,0x20,0x70,
 0xf0,0x10,0xf0,0x80,0xf0,0xf0,0x10,0xf0,0x10,0xf0,
 0x90,0x90,0xf0,0x10,0x10,0xf0,0x80,0xf0,0x10,0xf0,
 0xf0,0x80,0xf0,0x90,0xf0,0xf0,0x10,0x20,0x40,0x40,
 0xf0,0x90,0xf0,0x90,0xf0,0xf0,0x90,0xf0,0x10,0xf0,
 0xf0,0x90,0xf0,0x90,0x90,0xe0,0x90,0xe0,0x90,0xe0,
 0xf0,0x80,0x80,0x80,0xf0,0xe0,0x90,0x90,0x90,0xe0,
 0xf0,0x80,0xf0,0x80,0xf0,0xf0,0x80,0xf0,0x80,0x80};
unsigned int c8_size(void){return sizeof(struct chip8);}
void c8_reset(struct chip8 *s,unsigned int seed){
 unsigned int i; c8_u8 *p=(c8_u8*)s;
 for(i=0;i<sizeof(*s);i++)p[i]=0;
 for(i=0;i<80;i++)s->ram[0x50+i]=font[i];
 s->pc=0x200;s->rng=seed?seed:1;
}
static unsigned int instruction(struct chip8 *s){
 unsigned int op,x,y,n,kk,addr,a,b,i,j,p,mask,sum,key;
 if(s->pc>4094)return C8_MEMORY;
 op=(unsigned int)s->ram[s->pc]<<8|s->ram[s->pc+1];
 x=(op>>8)&15;y=(op>>4)&15;n=op&15;kk=op&255;addr=op&4095;
 a=s->v[x];b=s->v[y];s->pc+=2;
 switch(op>>12){
 case 0:
  if(op==0xe0){for(i=0;i<C8_FRAME_BYTES;i++)s->frame[i]=0;}
  else if(op==0xee){if(!s->sp)return C8_STACK;s->pc=s->stack[--s->sp];}
  else return C8_OPCODE;
  break;
 case 1:s->pc=addr;break;
 case 2:if(s->sp==16)return C8_STACK;s->stack[s->sp++]=s->pc;s->pc=addr;break;
 case 3:if(a==kk)s->pc+=2;break;
 case 4:if(a!=kk)s->pc+=2;break;
 case 5:if(n)return C8_OPCODE;if(a==b)s->pc+=2;break;
 case 6:s->v[x]=kk;break;
 case 7:s->v[x]=a+kk;break;
 case 8:
  switch(n){
  case 0:s->v[x]=b;break;
  case 1:s->v[x]=a|b;break;
  case 2:s->v[x]=a&b;break;
  case 3:s->v[x]=a^b;break;
  case 4:sum=a+b;s->v[x]=sum;s->v[15]=sum>255;break;
  case 5:s->v[x]=a-b;s->v[15]=a>=b;break;
  case 6:s->v[x]=a>>1;s->v[15]=a&1;break;
  case 7:s->v[x]=b-a;s->v[15]=b>=a;break;
  case 14:s->v[x]=a<<1;s->v[15]=a>>7;break;
  default:return C8_OPCODE;
  }break;
 case 9:if(n)return C8_OPCODE;if(a!=b)s->pc+=2;break;
 case 10:s->index=addr;break;
 case 11:s->pc=addr+s->v[0];break;
 case 12:s->rng^=s->rng<<13;s->rng^=s->rng>>17;s->rng^=s->rng<<5;s->v[x]=(s->rng>>24)&kk;break;
 case 13:
  if(!n)return C8_OPCODE;
  if(s->index>4096-n)return C8_MEMORY;
  /* Snapshot x/y before writing VF, including when either operand is VF. */
  s->v[15]=0;
  for(i=0;i<n;i++)for(j=0;j<8;j++)if(s->ram[s->index+i]&(128u>>j)){
   p=(((b+i)&31)*64+((a+j)&63));mask=128u>>(p&7);
   if(s->frame[p>>3]&mask)s->v[15]=1;
   s->frame[p>>3]^=mask;
  }
  break;
 case 14:
  key=a<16?((s->keys>>a)&1):0;
  if(kk==0x9e){if(key)s->pc+=2;}
  else if(kk==0xa1){if(!key)s->pc+=2;}
  else return C8_OPCODE;
  break;
 case 15:
  switch(kk){
  case 7:s->v[x]=s->delay;break;
  case 10:
   for(i=0;i<16;i++)if(s->keys&(1u<<i))break;
   if(i==16){s->pc-=2;return C8_WAIT;}s->v[x]=i;break;
  case 0x15:s->delay=a;break;
  case 0x18:s->sound=a;break;
  case 0x1e:s->index+=a;break;
  case 0x29:s->index=0x50+(a&15)*5;break;
  case 0x33:
   if(s->index>4093)return C8_MEMORY;
   s->ram[s->index]=a/100;s->ram[s->index+1]=(a/10)%10;s->ram[s->index+2]=a%10;break;
  case 0x55:case 0x65:
   if(s->index>4095-x)return C8_MEMORY;
   for(i=0;i<=x;i++)if(kk==0x55)s->ram[s->index+i]=s->v[i];else s->v[i]=s->ram[s->index+i];
   break;
  default:return C8_OPCODE;
  }break;
 }
 return C8_OK;
}
unsigned int c8_run(struct chip8 *s,unsigned int cycles,unsigned int ticks,unsigned int keys,unsigned int *executed){
 unsigned int status=C8_OK,i;*executed=0;
 /* Public core entry is bounded even outside the wire adapter. */
 if(cycles>C8_MAX_CYCLES)cycles=C8_MAX_CYCLES;
 if(ticks>60)ticks=60;
 s->keys=keys&65535;
 s->delay=ticks>=s->delay?0:s->delay-ticks;
 s->sound=ticks>=s->sound?0:s->sound-ticks;
 if(s->fault)return s->fault;
 for(i=0;i<cycles;i++){
  status=instruction(s);if(status!=C8_OK)break;
  ++*executed;++s->total;
 }
 if(status>C8_WAIT)s->fault=status;
 return status;
}
static unsigned int word(const c8_u8*p){return (unsigned int)p[0]|(unsigned int)p[1]<<8|(unsigned int)p[2]<<16|(unsigned int)p[3]<<24;}
static void put(c8_u8*p,unsigned int v){p[0]=v;p[1]=v>>8;p[2]=v>>16;p[3]=v>>24;}
unsigned int c8_request(struct chip8*s,const c8_u8*in,unsigned int n,c8_u8*out,unsigned int capacity){
 unsigned int op,cycles,keys,ticks,seed,i,status=C8_OK,executed=0;
 if(n<24||word(in)!=C8_MAGIC)return 1;
 op=word(in+4);cycles=word(in+8);keys=word(in+12);ticks=word(in+16);seed=word(in+20);
 if(op>1||cycles>C8_MAX_CYCLES||keys>65535||ticks>60)return 1;
 if(op==0){if(n<26||n>24+3584||cycles||keys||ticks)return 1;}
 else if(n!=24||seed)return 1;
 if(capacity<C8_REPLY_BYTES)return 2;
 if(op==0){c8_reset(s,seed);for(i=24;i<n;i++)s->ram[0x200+i-24]=in[i];}
 else status=c8_run(s,cycles,ticks,keys,&executed);
 put(out,C8_MAGIC);put(out+4,status);put(out+8,executed);put(out+12,s->total);
 put(out+16,s->pc);put(out+20,s->index);put(out+24,s->delay);put(out+28,s->sound);
 for(i=0;i<16;i++)out[32+i]=s->v[i];
 for(i=0;i<C8_FRAME_BYTES;i++)out[48+i]=s->frame[i];
 return 0;
}
