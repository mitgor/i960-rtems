/* Freeze task switching across the raw snapshot and exact lease validation.
 * No hardware state is changed or error flag cleared. Unknown DMA stays visible. */
#ifndef PP_AUDIT_LOCK
static unsigned pp_audit_lock(void){unsigned pc=31u<<16;__asm__ volatile("lda 0x1f0000,g0;modpc 0,g0,%0":"+r"(pc)::"g0","memory");return pc;}
static void pp_audit_unlock(unsigned pc){__asm__ volatile("lda 0x1f0000,g0;modpc 0,g0,%0":"+r"(pc)::"g0","memory");}
#define PP_AUDIT_LOCK() pp_audit_lock()
#define PP_AUDIT_UNLOCK(pc) pp_audit_unlock(pc)
#endif
static void pp_engine_report(unsigned*w){unsigned i,pc=PP_AUDIT_LOCK();
 extern unsigned frame_dma_report_snapshot(unsigned*);
 engine_snapshot(w);frame_dma_report_snapshot(w);
 for(i=0;i<6;i++)if(w[i])runtime_error|=0x100;
 w[16]=runtime_error;PP_AUDIT_UNLOCK(pc);
}
