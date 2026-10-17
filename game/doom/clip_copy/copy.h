#ifndef DOOM_CLIP_COPY_H
#define DOOM_CLIP_COPY_H
/* Doom's ceiling/floor clip arrays and openings are short-aligned, but their
 * word alignment may differ. Copy exactly count halfwords; never widen an
 * access across a neighboring allocation or drawseg boundary. */
static inline void doom_clip_copy(short *dst, const short *src, unsigned count)
{
    unsigned i = 0;
    for (; count - i >= 4; i += 4) {
        dst[i] = src[i]; dst[i+1] = src[i+1];
        dst[i+2] = src[i+2]; dst[i+3] = src[i+3];
    }
    for (; i < count; ++i) dst[i] = src[i];
}
#endif
