/*
 *  This file contains all assembly code for the i960 port of RTEMS.
 *
 *  COPYRIGHT (c) 1989-1999.
 *  On-Line Applications Research Corporation (OAR).
 *
 *  The license and distribution terms for this file may be
 *  found in the file LICENSE in this distribution or at
 *  http://www.rtems.com/license/LICENSE.
 *
 *  $Id: cpu_asm.S,v 1.8.4.1 2003/09/04 18:47:27 joel Exp $
 */
	.data
_ISR_reg_save:
	.word  0
	.word  0
	.word  0
	.word  0
	.word  0
	.word  0

          .text
/*
 * Format of i960ca Register structure
 */

.set REG_R0_PFP    , 0                # (r0)  Previous Frame Pointer
.set REG_R1_SP     , REG_R0_PFP+4     # (r1)  Stack Pointer
.set REG_PC        , REG_R1_SP+4      # (pc)  Processor Controls
.set REG_G8        , REG_PC+4         # (g8)  Global Register 8
.set REG_G9        , REG_G8+4         # (g9)  Global Register 9
.set REG_G10       , REG_G9+4         # (g10) Global Register 10
.set REG_G11       , REG_G10+4        # (g11) Global Register 11
.set REG_G12       , REG_G11+4        # (g12) Global Register 12
.set REG_G13       , REG_G12+4        # (g13) Global Register 13
.set REG_G14       , REG_G13+4        # (g14) Global Register 14
.set REG_G15_FP    , REG_G14+4        # (g15) Global Register 15
.set SIZE_REGS     , REG_G15_FP+4     # size of cpu_context_registers
                                      #    structure

/*
 *  void _CPU_Context_switch( run_context, heir_context )
 *
 *  This routine performs a normal non-FP context.
 */
          .align    4
          .globl    __CPU_Context_switch

__CPU_Context_switch:
          modpc     0,0,g2                   # get old intr level (PC)
          st        g2,REG_PC(g0)            # save pc
          stq       g8,REG_G8(g0)            # save g8-g11
          stq       g12,REG_G12(g0)          # save g12-g15
          stl       pfp,REG_R0_PFP(g0)       # save pfp, sp

restore:  flushreg                           # flush register cache
          ldconst   0x001f0000,g2            # g2 = PC mask
          ld        REG_PC(g1),g3            # thread->Regs.pc = pc;
          ldq       REG_G12(g1),g12          # restore g12-g15
          ldl       REG_R0_PFP(g1),pfp       # restore pfp, sp
          ldq       REG_G8(g1),g8            # restore g8-g11
          modpc     0,g2,g3                  # restore PC register
          ret

/*
 *  void _CPU_Context_restore( new_context )
 *
 *  This routine performs a normal non-FP context.
 */

        .globl __CPU_Context_restore
__CPU_Context_restore:
          mov       g0,g1                    # g0 = _Thread_executing
          b         restore

/*PAGE
 *  void _CPU_Context_save_fp_context( &fp_context_ptr )
 *  void _CPU_Context_restore_fp_context( &fp_context_ptr )
 *
 *  There is currently no hardware floating point for the i960.
 */

          .globl    __CPU_Context_save_fp
          .globl    __CPU_Context_restore_fp
__CPU_Context_save_fp:
__CPU_Context_restore_fp:
#if ( I960_HAS_FPU == 1 )
#error "Floating point support for i960 family has been implemented!!!"
#endif
          ret
