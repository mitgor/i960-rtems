/* Masked posts are finite pixel runs, unlike wrapping wall columns.
 * Fixed-point reciprocal rounding can put an edge sample just outside a post.
 * Clamp that sample to the edge; never read post padding or a neighboring lump.
 * Kept independent of Doom headers for boundary tests on both host and i960.
 */
#ifndef DOOM_BOUNDED_COLUMN_H
#define DOOM_BOUNDED_COLUMN_H
static inline int R_ColumnIndex(int frac, int post_length, int wall_wrap)
{
    int index = frac >> 16;
    if (post_length > 0) {
        if (index < 0) return 0;
        if (index >= post_length) return post_length - 1;
        return index;
    }
    return wall_wrap ? (index & 127) : index;
}
#endif
