#include "chip8.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static struct chip8 s;
static void op(unsigned int code){unsigned int n;s.ram[s.pc]=code>>8;s.ram[s.pc+1]=code;assert(c8_run(&s,1,0,s.keys,&n)==0);assert(n==1);}
static void put(unsigned char*p,unsigned int v){p[0]=v;p[1]=v>>8;p[2]=v>>16;p[3]=v>>24;}
int main(void){
 unsigned int n,i,j,seed=17,status;unsigned char in[3610],out[306];struct chip8 saved;
 assert(sizeof(c8_u32)==4&&sizeof(c8_u16)==2);
 c8_reset(&s,1);op(0x60fe);op(0x6103);op(0x8014);assert(s.v[0]==1&&s.v[15]==1);
 op(0x8015);assert(s.v[0]==254&&s.v[15]==0);
 op(0x8017);assert(s.v[0]==5&&s.v[15]==0);
 op(0x8016);assert(s.v[0]==2&&s.v[15]==1);op(0x801e);assert(s.v[0]==4&&s.v[15]==0);
 /* VF operand aliasing: flags must use original register values. */
 s.v[15]=255;s.v[1]=1;op(0x8f14);assert(s.v[15]==1);
 op(0xa300);op(0x60e7);op(0xf033);assert(s.ram[0x300]==2&&s.ram[0x301]==3&&s.ram[0x302]==1);
 op(0xf155);s.v[0]=0;s.v[1]=0;op(0xf165);assert(s.v[0]==231&&s.v[1]==1&&s.index==0x300);
 op(0x2220);assert(s.pc==0x220&&s.sp==1);op(0x00ee);assert(s.sp==0);
 c8_reset(&s,1);s.ram[0x300]=0xc0;s.index=0x300;s.v[0]=63;s.v[1]=31;op(0xd011);
 assert(s.frame[248]==128&&s.frame[255]==1&&s.v[15]==0);op(0xd011);assert(s.v[15]==1);
 for(i=0;i<256;i++)assert(s.frame[i]==0);
 s.delay=5;s.sound=2;assert(c8_run(&s,0,3,0,&n)==0&&s.delay==2&&s.sound==0);
 s.ram[s.pc]=0xf2;s.ram[s.pc+1]=0x0a;i=s.pc;
 assert(c8_run(&s,1000,0,0,&n)==C8_WAIT&&s.pc==i&&n==0);
 assert(c8_run(&s,1,0,1u<<9,&n)==0&&s.v[2]==9&&n==1);
 c8_reset(&s,1);op(0x1200);assert(c8_run(&s,1000000,0,0,&n)==0&&n==1000);
 c8_reset(&s,1);s.pc=4095;assert(c8_run(&s,1,0,0,&n)==C8_MEMORY);
 c8_reset(&s,1);s.ram[0x200]=0x00;s.ram[0x201]=0xee;assert(c8_run(&s,1,0,0,&n)==C8_STACK);
 c8_reset(&s,1);s.ram[0x200]=0x22;s.ram[0x201]=0;assert(c8_run(&s,1000,0,0,&n)==C8_STACK&&n==16);
 c8_reset(&s,1);s.index=4095;s.ram[0x200]=0xf0;s.ram[0x201]=0x33;
 assert(c8_run(&s,1,0,0,&n)==C8_MEMORY);assert(c8_run(&s,1000,0,0,&n)==C8_MEMORY&&n==0);
 memset(in,0,sizeof(in));memset(out,0xa5,sizeof(out));put(in,C8_MAGIC);in[24]=0x12;in[25]=0;
 assert(c8_request(&s,in,26,out+1,304)==0);assert(out[0]==0xa5&&out[305]==0xa5);
 saved=s;assert(c8_request(&s,in,26,out,303)==2);assert(!memcmp(&s,&saved,sizeof(s)));
 put(in+4,1);put(in+8,1001);assert(c8_request(&s,in,24,out,304)==1);assert(!memcmp(&s,&saved,sizeof(s)));
 put(in+8,1000);assert(c8_request(&s,in,24,out,304)==0&&s.total==1000);
 /* Every opcode with adversarial memory/index/stack bounds under ASan/UBSan. */
 for(i=0;i<65536;i++){
  c8_reset(&s,i);s.index=4095;s.v[0]=255;s.v[15]=255;
  s.ram[0x200]=i>>8;s.ram[0x201]=i;
  status=c8_run(&s,1,60,65535,&n);assert(status<=C8_STACK&&n<=1);
 }
 /* Deterministic random programs, each bounded independently. */
 for(i=0;i<1000;i++){
  c8_reset(&s,i);
  for(j=512;j<4096;j++){seed=seed*1664525u+1013904223u;s.ram[j]=seed>>24;}
  status=c8_run(&s,1000,1,i,&n);assert(status<=C8_STACK&&n<=1000);
 }
 puts("CHIP-8: arithmetic, aliasing, stack, memory, wrap/collision, timer, key wait, protocol, all 65536 opcodes and 1000 random programs passed (ASan/UBSan)");
 return 0;
}
