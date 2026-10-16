#include "ping_protocol.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void reject_single_byte_changes(const uint8_t original[64])
{
    uint8_t m[64];
    uint32_t nonce = 0;
    size_t i;
    int rejected = 0;
    for (i = 2; i < 64; ++i) {
        /* Nonce changes remain valid unless the whole nonce becomes zero. */
        if (i >= 28 && i < 32) continue;
        memcpy(m, original, sizeof(m));
        m[i] ^= 1u;
        assert(ar160_ping_validate(m, sizeof(m), &nonce) != AR160_PING_ACCEPT);
        ++rejected;
    }
    assert(rejected == 58);
}

int main(void)
{
    uint8_t m[64];
    static const uint8_t expected[64] = {
        0xfe, 0xff, 0x20, 0x40, [21] = 0x8f, [22] = 1, [23] = 1,
        [24] = 'I', [25] = '9', [26] = '6', [27] = '0',
        [28] = 0x78, [29] = 0x56, [30] = 0x34, [31] = 0x12
    };
    uint32_t nonce = 0;
    ar160_ping_build(m, 0xfffeu, 0x12345678u);
    assert(memcmp(m, expected, sizeof(expected)) == 0);
    assert(ar160_ping_validate(m, sizeof(m), &nonce) == AR160_PING_ACCEPT);
    assert(nonce == 0x12345678u);
    assert(m[0] == 0xfe && m[1] == 0xff && m[21] == 0x8f);
    reject_single_byte_changes(m);
    assert(ar160_ping_validate(m, 63, &nonce) == AR160_PING_BAD_LENGTH);
    assert(ar160_ping_validate(NULL, 64, &nonce) == AR160_PING_BAD_LENGTH);
    assert(ar160_ping_validate(m, 64, NULL) == AR160_PING_BAD_LENGTH);
    ar160_ping_build(m, 1, 0);
    assert(ar160_ping_validate(m, sizeof(m), &nonce) == AR160_PING_BAD_NONCE);
    puts("PING admission: valid packet, 58 single-byte mutations, length and nonce checks passed");
    return 0;
}
