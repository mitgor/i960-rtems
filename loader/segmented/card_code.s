    .text
    .globl _segment_code
    .globl _segment_end
_segment_code:
    ld (g0),g0
    lda 0xa5a5a5a5,g1
    xor g0,g1,g0
    ret
_segment_end:
