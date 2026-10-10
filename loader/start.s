# i960 reset entry for the flash loader.
# The core enters here (firstIP, set by mkimage.py) having loaded the stock PRCB.
# We relocate the stack into the 1 KB internal data RAM (0x0..0x3FF), which exists
# at reset with no memory-controller init, then call the C loader. Frames are
# 64-byte aligned; 0x40 leaves the reserved low words alone and gives ~448 bytes
# of stack below the demo payload at 0x200. This is an UNVERIFIED budget:
# inspect generated code and validate
# the inherited register-cache / flushreg assumptions before hardware bring-up.
    .text
    .globl _start
_start:
    lda     0x40, fp          # frame pointer -> internal data RAM
    lda     0x40, sp          # stack pointer (grows up)
    flushreg                  # sync the local-register cache to the new stack
    mov     0, g14            # GCC i960 ABI uses g14 as zero on C function entry
    call    _loader_main      # single call; never returns
.Lhang:
    b       .Lhang
