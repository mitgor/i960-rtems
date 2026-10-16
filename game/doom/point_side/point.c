/* Exact 32-bit Doom BSP partition test. GPL-2.0-or-later, derived from
 * Doom's R_PointOnSide. Keep each i960 compare/test in one asm statement:
 * GCC 3.3 can otherwise schedule a CC-writing compare/branch between them.
 * Unsigned deltas define the original target's two's-complement wrapping. */
#include "r_local.h"
static __inline__ __attribute__((always_inline)) int signed32(unsigned v)
{
    return (int)(v & 0x7fffffffu) - (int)(v >> 31) * 2147483647 - (int)(v >> 31);
}
static __inline__ __attribute__((always_inline)) int le(int a, int b)
{
#ifdef __i960__
    int result;
    __asm__ volatile ("cmpi %1,%2\n\ttestle %0" : "=r" (result) : "r" (a), "r" (b) : "cc");
    return result;
#else
    return a <= b;
#endif
}
static __inline__ __attribute__((always_inline)) unsigned positive(unsigned v)
{
    return ((v | (0u-v)) >> 31) & ((v >> 31) ^ 1u);
}
int R_PointOnSide(fixed_t x, fixed_t y, node_t *node)
{
    unsigned nx=(unsigned)node->dx, ny=(unsigned)node->dy;
    unsigned dx,dy; int left,right,hx,hy;
    if (!nx) return le(x,node->x) ? positive(ny) : ny >> 31;
    if (!ny) return le(y,node->y) ? nx >> 31 : positive(nx);
    dx=(unsigned)x-(unsigned)node->x;
    dy=(unsigned)y-(unsigned)node->y;
    if ((ny^nx^dx^dy)>>31) return (ny^dx)>>31;
    /* Explicit arithmetic >>16, without implementation-defined signed shift. */
    hx=(int)(nx>>16)-(int)(nx>>31)*65536;
    hy=(int)(ny>>16)-(int)(ny>>31)*65536;
    left=signed32((unsigned)((unsigned long long)((long long)hy*signed32(dx))>>16));
    right=signed32((unsigned)((unsigned long long)((long long)signed32(dy)*hx)>>16));
    return le(left,right);
}
