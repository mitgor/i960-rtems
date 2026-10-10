# Non-returning proof of DRAM execution. OMR0 retains the GO acknowledgement.
    .text
    .globl _start
_start:
    lda 0xbeef00ee,g0
    st g0,0x131c
.Lstop:
    b .Lstop
