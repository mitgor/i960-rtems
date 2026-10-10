# v2: intercept BEFORE EBCR clears retry. Leave stock boot block untouched.
    .text
    .globl _start
_start:
    intdis
    lda 0x84003000,g0
    st g0,0xc004e834
    lda _postinit,g0
    st g0,0xc004e838
    icctl 2,0,g0
    mov 0,g14
    bx 0xc004a2e0
_postinit:
    intdis
    mov 0,g14
    dcctl 0,0,g0
    icctl 2,0,g0
    st g14,0xff000308             # disable core timer 0
    st g14,0xff000318             # disable core timer 1
    st g14,0x1274             # ERLR=0: no expansion-ROM aperture (manual 16.7.31)
    lda 0xff,g0
    st g0,0x1334              # mask MU outbound interrupt sources
    ld 0x1404,g0              # three DMA status registers; bit 10 = active
    ld 0x1444,g1
    ld 0x1484,g2
    or g0,g1,g3
    or g2,g3,g3
    bbs 10,g3,.Ldma_busy
    # Idle channels may still be enabled; disable without starting/aborting DMA.
    st g14,0x1400
    st g14,0x1440
    st g14,0x1480
    ld 0x1404,g0
    ld 0x1444,g1
    ld 0x1484,g2
    or g0,g1,g3
    or g2,g3,g3
    bbs 10,g3,.Ldma_busy
    lda 8,g0
    stos g0,0x1040            # original stock EBCR value, after ROM suppression
    call _loader_main
.Lhalt:
    b .Lhalt
.Ldma_busy:
    st g3,0x131c              # diagnostic status; do not publish READY
    lda 0x60ef,g0
    st g0,0x1318
    lda 8,g0
    stos g0,0x1040            # permit host to see failure, no DMA cancellation
    b .Lhalt
