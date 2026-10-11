#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "lifetime.h"
int main(void){struct irq_lifetime s[2]={{1,0x1000,0x3000,0,0,0,0,0,0,0},{2,0x5000,0x7000,0,0,0,0,0,0,0}},copy;
 assert(lifetime_drained(s));assert(lifetime_enter(s,1,0x1800,0x142002,0x9002,0xf2));
 copy=s[0];assert(!lifetime_enter(s,1,0x1900,1,2,0xf2));assert(!memcmp(&copy,s,sizeof(copy)));
 assert(lifetime_enter(s+1,2,0x5800,0x142002,0x9004,0xf2));assert(!lifetime_drained(s));
 assert(!lifetime_leave(s,2,0x1800,0x142002,0x9002,0xf2));
 assert(!lifetime_leave(s,1,0x1810,0x142002,0x9002,0xf2));
 assert(!lifetime_leave(s,1,0x1800,0x142002,0x9004,0xf2));
 assert(lifetime_leave(s,1,0x1800,0x142002,0x9002,0xf2));assert(!lifetime_drained(s));
 assert(lifetime_enter(s,1,0x1800,0x142002,0x9004,0xf2));
 assert(lifetime_leave(s+1,2,0x5800,0x142002,0x9004,0xf2));
 assert(lifetime_leave(s,1,0x1800,0x142002,0x9004,0xf2));assert(lifetime_drained(s));
 assert(!lifetime_enter(s,0,0x1800,1,2,0xf2));assert(!lifetime_enter(s,1,0x1000,1,2,0xf2));
 assert(!lifetime_enter(s,1,0x2fd0,1,2,0xf2));assert(!lifetime_enter(s,1,0x1801,1,2,0xf2));assert(!lifetime_enter(s,1,0x1800,1,2,0xf1));
 puts("Two owned IRQ continuations: interleaved resume, owner/frame/AC mismatch, reentry, bounds and drain-before-release passed");return 0;}
