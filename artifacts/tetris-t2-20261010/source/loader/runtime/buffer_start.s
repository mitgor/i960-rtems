/* Stable raw-binary entry before compiler-emitted out-of-line helpers. */
    .text
    .globl _buffer_start
_buffer_start:
    b _payload
