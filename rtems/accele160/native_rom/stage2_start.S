/* Fixed stock boot-block call target; preserve g0/g1 and the callx return. */
 .section .entry,"ax"
 .globl _stage2_entry
_stage2_entry:
 b _stage2
