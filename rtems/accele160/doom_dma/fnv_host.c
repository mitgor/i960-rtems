#include <stddef.h>
#include <stdint.h>
uint32_t frame_fnv(const unsigned char *p, size_t n) {
    uint32_t h = UINT32_C(2166136261);
    for (size_t i = 0; i < n; ++i) h = (h ^ p[i]) * UINT32_C(16777619);
    return h;
}
