/* First rejection only. Diagnostic data confers no interrupt/task ownership. */
#ifdef I960_DOOM_ENGINE
volatile unsigned engine_irq_reject[12];
void engine_irq_drain_record(void){extern volatile unsigned switch_threads[2],switch_active[2];unsigned fp,pc;
 if(engine_irq_reject[0])return;
 __asm__ volatile("mov fp,%0":"=r"(fp));__asm__ volatile("modpc 0,0,%0":"=r"(pc));
 engine_irq_reject[1]=3;engine_irq_reject[2]=0;engine_irq_reject[3]=switch_active[0];engine_irq_reject[4]=switch_active[1];engine_irq_reject[5]=fp;engine_irq_reject[6]=pc;engine_irq_reject[9]=switch_threads[0];engine_irq_reject[10]=switch_threads[1];engine_irq_reject[11]=1;engine_irq_reject[0]=0x31524a49u;
}
#endif
