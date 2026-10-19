#include <assert.h>
#include <stdio.h>
static unsigned reads;
static unsigned read16(unsigned a);
#define QC_READ16(a) read16(a)
#include "qlogic_chip.h"
static unsigned read16(unsigned a){assert(reads<12);assert(a==0x8bf00000+at_qc_offsets[reads%6]);return ++reads;}
int main(void){unsigned r[1024]={0},i,j;
 unsigned fields[]={325,328,330,331,334,357,359,358,360};
 unsigned values[]={0,5,0x10161077,2,0xfff00000,0,14,0xc0600d00,0x8bf00000};
 for(i=0;i<9;i++)r[fields[i]]=values[i];
 r[383]=r[416]=0xa5a5a5a5;
 at_qlogic_chip(r,23,4,0);assert(reads==12&&r[389]==0&&r[390]==12);
 assert(r[383]==0xa5a5a5a5&&r[416]==0xa5a5a5a5);
 for(i=0;i<12;i++)assert(r[392+i]==i+1);
 for(i=0;i<9;i++){
  r[fields[i]]=values[i]^2;reads=0;at_qlogic_chip(r,23,5,1);
  assert(!reads&&r[389]==1&&!r[390]);
  for(j=392;j<416;j++)assert(!r[j]);
  r[fields[i]]=values[i];
 }
 puts("chip: exact 12 ordered halfword accesses, nine refusal gates, bounds passed");
 return 0;
}
