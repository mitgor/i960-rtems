/* One live ISR continuation only. The hardware frame is never relocated. */
#define IRQ_AREA_SIZE 16512u
unsigned char irq_owned_area[IRQ_AREA_SIZE] __attribute__((aligned(16)));
volatile unsigned int irq_owned_active,irq_owned_entries,irq_owned_fault;
volatile unsigned int irq_owned_low,irq_owned_high,irq_owned_entry_fp,irq_owned_pc,irq_owned_ac,irq_owned_vector;
unsigned int irq_probe_gbefore[16],irq_probe_gafter[16],irq_probe_lbefore[16],irq_probe_lafter[16];
unsigned int irq_probe_controls[4],irq_probe_fail;
extern void irq_context_probe(void);
static void irq_owned_prepare(void){
 memset(irq_owned_area,0xa5,sizeof(irq_owned_area));
 irq_owned_active=irq_owned_entries=irq_owned_fault=0;
 irq_owned_low=0xffffffffu;irq_owned_high=0;irq_probe_fail=0;
}
static void irq_measure(void){unsigned int sp;
 __asm__ volatile("mov sp,%0":"=r"(sp));
 if(sp<irq_owned_low)irq_owned_low=sp;if(sp>irq_owned_high)irq_owned_high=sp;
 if(sp<(unsigned int)irq_owned_area+192||sp>(unsigned int)irq_owned_area+IRQ_AREA_SIZE-64)irq_owned_fault|=1;
}
void irq_owned_enter(unsigned int fp){
 unsigned int pc;irq_measure();irq_owned_entries++;irq_owned_entry_fp=fp;
 irq_owned_pc=REG(fp-16);irq_owned_ac=REG(fp-12);irq_owned_vector=REG(fp-8);
 __asm__ volatile("modpc 0,0,%0":"=r"(pc));
 if(pc&1)irq_owned_fault|=2;
}
/* Force register-window spills on the owned stack, checking every local buffer
 * during unwind. No tail-call optimization is possible across the checks. */
#ifdef I960_CONTEXT_TEST
static unsigned int irq_deep(unsigned int depth){volatile unsigned int pad[16];unsigned int i,sum=0;
 irq_measure();for(i=0;i<16;i++)pad[i]=depth*256+i;
 if(depth)sum=irq_deep(depth-1);
 for(i=0;i<16;i++){if(pad[i]!=depth*256+i)irq_owned_fault|=4;sum+=pad[i];}
 return sum;
}
#endif
void irq_owned_leave(void){unsigned int i,tc;unsigned int *saved=(unsigned int*)(irq_owned_area+64);
 irq_measure();
 if(REG(irq_owned_entry_fp-16)!=saved[17]||REG(irq_owned_entry_fp-12)!=saved[18]||REG(irq_owned_entry_fp-8)!=saved[19])irq_owned_fault|=8;
 for(i=0;i<64;i++)if(irq_owned_area[i]!=0xa5||irq_owned_area[IRQ_AREA_SIZE-64+i]!=0xa5)irq_owned_fault|=16;
 __asm__ volatile("modtc 0,0,%0":"=r"(tc));
 if((tc^saved[16])&0x0f000000u)irq_owned_fault|=32;
#ifdef I960_CONTEXT_TEST
 /* Exercise explicit restoration of a writable TC mode bit; PC.te is clear. */
 if(!(irq_owned_fault&2)){unsigned int m=128,v=tc^128,old;__asm__ volatile("modtc %1,%2,%0":"=r"(old):"r"(m),"r"(v));}
#endif
}
#ifdef I960_CONTEXT_TEST
static void irq_probe_check(void){unsigned int i;
 for(i=0;i<16;i++)if(irq_probe_gbefore[i]!=irq_probe_gafter[i])irq_probe_fail|=1;
 /* RIP is legitimately updated by interrupt calls; r3 is the bounded counter. */
 for(i=0;i<16;i++)if(i!=2&&i!=3&&irq_probe_lbefore[i]!=irq_probe_lafter[i])irq_probe_fail|=2;
 if(irq_probe_controls[0]!=irq_probe_controls[1])irq_probe_fail|=4;
 if(irq_probe_controls[2]!=irq_probe_controls[3])irq_probe_fail|=8;
}
static void irq_probe_deep(unsigned int depth){volatile unsigned int pad[16];unsigned int i;
 for(i=0;i<16;i++)pad[i]=depth*128+i;
 if(depth)irq_probe_deep(depth-1);else irq_context_probe();
 for(i=0;i<16;i++)if(pad[i]!=depth*128+i)irq_probe_fail|=16;
}

#endif
